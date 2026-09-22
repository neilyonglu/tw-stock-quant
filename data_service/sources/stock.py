"""個股 raw 資料：K 線/成交量/基本面/五檔。只做「抓取」，不算 SMA/RSI/MACD 等指標
（那些是後端該做的計算，見 PROJECT.md「架構：中台 / 前端 / 後端」）。
搬自舊 src/api/{get_stock_data,get_stock_profile,get_orderbook}.py。
"""
import calendar
import logging

import pandas as pd
import twstock
import yfinance as yf

from data_service import store
from data_service.cache import ttl_cache

logger = logging.getLogger("data_service.candles")
if not logger.handlers:  # uvicorn 不會幫 app logger 接 handler，自己接一個
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
    logger.propagate = False

INTRADAY_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}

# 只有「歷史」K 線落地 SQLite（設計見 plan.md Phase 1a）；分鐘 K 屬即時，維持純記憶體
PERSIST_INTERVALS = {"1d", "1wk", "1mo"}

# 增量抓取時故意往回多抓的重疊根數：重疊處 close 對不上 → 除權息還原價平移了
TAIL_OVERLAP = 5
ADJUST_TOLERANCE = 0.001  # 相對差 >0.1% 視為平移（浮點誤差遠小於此）

_PERIOD_MONTHS = {"1mo": 1, "3mo": 3, "6mo": 6, "1y": 12, "2y": 24, "5y": 60, "10y": 120}
# 「首根可以比切點晚多少天」的合理上限（月線首根最多晚一個月＋緩衝）；
# 超過就代表資料源根本沒有更早的資料（新上市股），記進 source_meta 避免反覆全抓
_SOURCE_START_MARGIN_DAYS = {"1d": 7, "1wk": 14, "1mo": 45}

# 台股慣例：紅漲綠跌（跟美股的 green-up / red-down 相反）
STOCK_UP = "#EF5350"  # 漲：紅
STOCK_DOWN = "#26A69A"  # 跌：綠


def _fmt_time(ts, is_intraday: bool):
    """Intraday → unix timestamp（假 UTC，見 get_stock_data.py 說明）; 日/週/月 → "YYYY-MM-DD"。"""
    if is_intraday:
        return calendar.timegm(ts.timetuple())
    return ts.strftime("%Y-%m-%d")


def _tick_size(price: float) -> float:
    """TWSE 股票最小跳動單位（簡化版，足夠估算漲跌停價用）。"""
    if price < 10:
        return 0.01
    if price < 50:
        return 0.05
    if price < 100:
        return 0.1
    if price < 500:
        return 0.5
    if price < 1000:
        return 1.0
    return 5.0


def _limit_prices(prev_close: float) -> tuple[float, float]:
    """漲跌停價估算：前收盤 ±10%，再依跳動單位取整。"""
    raw_up = prev_close * 1.1
    raw_down = prev_close * 0.9
    tick_up = _tick_size(raw_up)
    tick_down = _tick_size(raw_down)
    limit_up = (raw_up // tick_up) * tick_up
    limit_down = -(-raw_down // tick_down) * tick_down
    return round(limit_up, 2), round(limit_down, 2)


def _yf_rows(ticker: str, interval: str, is_intraday: bool, **history_kwargs) -> list[dict]:
    """打 yfinance，回傳統一的 row dicts（原始精度）。空資料回 []。"""
    df = yf.Ticker(f"{ticker}.TW").history(interval=interval, **history_kwargs)
    # 交易日當天還沒收盤時，yfinance 會多回傳一筆 OHLC 全是 NaN 的列，留著會讓
    # json.dumps 印出裸 NaN token，前端 JSON.parse 直接炸掉。
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return [
        {
            "time": _fmt_time(idx, is_intraday),
            "open": float(r["Open"]),
            "high": float(r["High"]),
            "low": float(r["Low"]),
            "close": float(r["Close"]),
            # 罕見的 Volume NaN 一律當 0：進 JSON 的裸 NaN 會炸掉前端 JSON.parse
            "volume": int(r["Volume"]) if r["Volume"] == r["Volume"] else 0,
        }
        for idx, r in df.iterrows()
    ]


@ttl_cache(seconds=300)
def _prev_daily_close(ticker: str) -> float | None:
    """漲跌停價的計算基準：前一交易日收盤價。

    這是「日」的概念——看 5 分線、週線、月線時，當天的漲跌停價一樣是用前一交易日
    收盤價算的，不是用前一根 K 棒。所以這裡固定抓日線，不跟著顯示週期走。

    （原本 _render() 直接拿輸出清單的 rows[-2]，等於看 5 分線時用前一根 5 分 K、
    看月線時用上個月收盤當基準，同一支股票同一天會因為選了不同週期而顯示四種
    不同的漲跌停價，只有日線碰巧是對的。）

    抓不到就回 None，呼叫端會讓 limit_up/limit_down 也是 null——寧可不顯示，
    也不要給一個看起來合理的錯價位。
    """
    rows = _yf_rows(ticker, "1d", False, period="5d")
    if not rows:
        return None
    today = pd.Timestamp.now(tz="Asia/Taipei").strftime("%Y-%m-%d")
    if rows[-1]["time"] == today:
        # 最後一根是今天（盤中或今日已收盤）→ 基準是前一個交易日
        return rows[-2]["close"] if len(rows) >= 2 else None
    # 最後一根不是今天（週末/假日/停牌）→ 那根就是最近的完整交易日，它自己是基準
    return rows[-1]["close"]


def _render(rows: list[dict], prev_close: float | None, stale_adjust: bool = False) -> dict:
    """row dicts → API 回傳 JSON。四捨五入到 2 位在這裡做（與舊行為一致）。

    prev_close 由呼叫端傳入（前一交易日收盤價，見 _prev_daily_close），不從 rows
    推——rows 是依 period 過濾後的顯示用清單，它的倒數第二根不一定是前一交易日。

    stale_adjust=True 代表偵測到除權息但重抓失敗，這批價格仍是平移前的舊還原價，
    呼叫端（尤其是回測）應該知道這件事，不要當成正確資料用。
    """
    candles = [
        {
            "time": r["time"],
            "open": round(r["open"], 2),
            "high": round(r["high"], 2),
            "low": round(r["low"], 2),
            "close": round(r["close"], 2),
        }
        for r in rows
    ]
    volume = [
        {
            "time": r["time"],
            "value": float(r["volume"]),
            "color": STOCK_UP if r["close"] >= r["open"] else STOCK_DOWN,
        }
        for r in rows
    ]
    limit_up, limit_down = _limit_prices(prev_close) if prev_close is not None else (None, None)
    return {
        "candles": candles,
        "volume": volume,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "stale_adjust": stale_adjust,
    }


def _period_cutoff(period: str) -> pd.Timestamp | None:
    """period 字串 → 起算日（台北時區、當日 00:00）。'max' 或看不懂的 → None（永遠全抓）。"""
    today = pd.Timestamp.now(tz="Asia/Taipei").normalize()
    months = _PERIOD_MONTHS.get(period)
    if months is not None:
        return today - pd.DateOffset(months=months)
    if period == "ytd":
        return today.replace(month=1, day=1)
    if period.endswith("d") and period[:-1].isdigit():
        return today - pd.Timedelta(days=int(period[:-1]))
    return None


def _serve_start(cutoff: pd.Timestamp, interval: str) -> str:
    """切點 → 該從哪天開始出資料。照 yfinance 語意（用 2330 基準實測驗證）：
    日線＝首根 ts >= 切點；週線＝含切點那一週的週一那根也要算；
    月線＝切點後的下一個月初才是首根（切點正好是 1 號則含當月）。"""
    if interval == "1wk":
        cutoff = cutoff - pd.Timedelta(days=cutoff.weekday())
    elif interval == "1mo" and cutoff.day != 1:
        cutoff = cutoff + pd.offsets.MonthBegin(1)
    return cutoff.strftime("%Y-%m-%d")


def _front_fill_impossible(ticker: str, interval: str, cov_first: str) -> bool:
    """庫存起點已經是資料源的最早資料 → 想要更早的也抓不到，不用白抓。"""
    known = store.source_start(ticker, interval)
    return known is not None and cov_first <= known


def _maybe_record_source_start(
    ticker: str, interval: str, period: str, cutoff: pd.Timestamp | None, first_ts: str
) -> None:
    """全抓後首根比切點晚太多 → 資料源沒有更早的了（新上市股），記下來。"""
    if period == "max":
        store.record_source_start(ticker, interval, first_ts)  # max 的首根就是最早資料，確定
        return
    if cutoff is None:
        return
    margin = pd.Timedelta(days=_SOURCE_START_MARGIN_DAYS[interval])
    if pd.Timestamp(first_ts, tz="Asia/Taipei") > cutoff + margin:
        store.record_source_start(ticker, interval, first_ts)


def _fetch_candles_persistent(ticker: str, period: str, interval: str) -> dict:
    """日/週/月 K 的三步查找：SQLite 查已存區間 → 只跟 yfinance 要缺口 → upsert 回存。
    設計（含除權息偵測）見 plan.md Phase 1a。"""
    yft = f"{ticker}.TW"
    cutoff = _period_cutoff(period)
    start_str = _serve_start(cutoff, interval) if cutoff is not None else None
    cov = store.coverage(yft, interval)

    # 庫存起點已是資料源的最早資料 → 不管要多早（含 period=max）都不必全抓
    have_all_history = cov is not None and _front_fill_impossible(yft, interval, cov[0])
    wants_earlier = start_str is None or (cov is not None and start_str < cov[0])

    if cov is None or (wants_earlier and not have_all_history):
        # 全抓：庫是空的／要的區間比庫存更早（含首次 period=max）。直接回抓到的內容
        # （跟改動前的行為逐 byte 一致），寫入 SQLite 是順手的副作用。
        rows = _yf_rows(ticker, interval, False, period=period)
        if not rows:
            return {"error": f"No data found for {ticker}.TW"}
        store.upsert(yft, interval, rows)
        _maybe_record_source_start(yft, interval, period, cutoff, rows[0]["time"])
        logger.info("%s %s %s: 全抓 %d 根（%s）", yft, interval, period, len(rows),
                    "庫空" if cov is None else "要補更早區間")
        return _render(rows, _prev_daily_close(ticker))

    # 增量：從庫存倒數第 TAIL_OVERLAP 根抓起（故意重疊，用來偵測除權息）
    overlap_start = store.tail_ts(yft, interval, TAIL_OVERLAP)
    new_rows = _yf_rows(ticker, interval, False, start=overlap_start)

    if not new_rows:
        # 外部來源暫時抓不到 → 歷史 K 線用庫存頂上（歷史不會過期），記一筆警告
        rows = store.rows_since(yft, interval, start_str)
        if not rows:
            return {"error": f"No data found for {ticker}.TW"}
        logger.warning("%s %s: yfinance 回空，以庫存 %d 根回應", yft, interval, len(rows))
        return _render(rows, _prev_daily_close(ticker))

    stored_closes = store.closes_since(yft, interval, overlap_start)
    adjusted = any(
        r["time"] in stored_closes
        and stored_closes[r["time"]] != 0
        and abs(r["close"] / stored_closes[r["time"]] - 1) > ADJUST_TOLERANCE
        for r in new_rows
    )
    stale_adjust = False
    if adjusted:
        # 除權息：還原價整條平移了，庫存跟新資料對不上 → 已存區間整段重抓覆寫
        logger.info("%s %s: 重疊處 close 對不上（除權息還原），整段重抓", yft, interval)
        full_rows = _yf_rows(ticker, interval, False, start=cov[0])
        if full_rows:
            store.upsert(yft, interval, full_rows)
        else:
            # 重抓失敗不能裝沒事：本次回應仍是平移前的舊還原價。除了記 log，回應本身
            # 也要帶 stale_adjust 標記——只寫 server log 的話，呼叫端（含隊友的回測
            # 系統）根本無從得知這批價格是錯的，可能拿去跑出錯的回測績效。
            logger.warning("%s %s: 除權息整段重抓失敗（yfinance 回空），本次回應仍為舊還原價",
                           yft, interval)
            stale_adjust = True
    else:
        store.upsert(yft, interval, new_rows)

    rows = store.rows_since(yft, interval, start_str)
    if not rows:
        return {"error": f"No data found for {ticker}.TW"}
    logger.info("%s %s %s: 庫存命中，向 yfinance 只要了 %d 根，回 %d 根",
                yft, interval, period, len(new_rows), len(rows))
    return _render(rows, _prev_daily_close(ticker), stale_adjust=stale_adjust)


@ttl_cache(seconds=60)
def fetch_candles(ticker: str, period: str, interval: str) -> dict:
    """raw OHLCV + 成交量 + 漲跌停價，不含任何技術指標。
    日/週/月 K 走 SQLite 持久化路徑；分鐘 K 等即時資料維持「每次現抓＋記憶體 TTL」。"""
    is_intraday = interval in INTRADAY_INTERVALS
    if not is_intraday and interval in PERSIST_INTERVALS:
        return _fetch_candles_persistent(ticker, period, interval)

    rows = _yf_rows(ticker, interval, is_intraday, period=period)
    if not rows:
        return {"error": f"No data found for {ticker}.TW"}
    return _render(rows, _prev_daily_close(ticker))


@ttl_cache(seconds=3600)
def _stock_index() -> list[tuple[str, str]]:
    """(代碼, 名稱) 清單，只留一般股票，排除權證/ETF/特別股等——twstock.codes 裡
    41000+ 筆多數是權證，全部搜尋會回一堆使用者用不到的雜訊。twstock 代碼表本身
    可能過期（新掛牌查不到），跟 get_stock_data.py 的 _company_name() 用同一份表。
    """
    return [(c.code, c.name) for c in twstock.codes.values() if c.type == "股票"]


def search_stocks(query: str, limit: int = 8) -> list[dict]:
    """依代碼前綴或名稱關鍵字搜尋股票。代碼完全符合 > 代碼前綴符合 > 名稱包含，同組內維持原順序。"""
    q = query.strip()
    if not q:
        return []

    def rank(item: tuple[str, str]) -> int:
        code, name = item
        if code == q:
            return 0
        if code.startswith(q):
            return 1
        if q in name:
            return 2
        return 3

    matches = [item for item in _stock_index() if rank(item) < 3]
    matches.sort(key=rank)
    return [{"ticker": code, "name": name} for code, name in matches[:limit]]


@ttl_cache(seconds=1800)
def fetch_profile(ticker: str) -> dict:
    """產業別/上市櫃別來自 twstock（本地查表），其餘來自 yfinance .info。
    月營收沒有真實來源（Phase 4 才接 CasualMarket），不在這裡回傳——由前端補 mock。
    """
    code_info = twstock.codes.get(ticker)
    industry = code_info.group if code_info else "未知"
    listed_market = "上市" if code_info and code_info.market == "上市" else "上櫃"

    info = yf.Ticker(f"{ticker}.TW").info

    market_cap = info.get("marketCap")
    shares = info.get("sharesOutstanding")

    return {
        "industry": industry,
        "listed_market": listed_market,
        # 缺值一律 None（跟本函式其餘欄位一致）。原本回 0 會被畫面顯示成「市值 0 億」，
        # 看起來像真的查到了一個極小的市值，而不是「查不到」。
        "market_cap": round(market_cap / 1e8, 1) if market_cap else None,
        "shares_outstanding": round(shares / 1e8, 2) if shares else None,
        "pe_ratio": round(info["trailingPE"], 2) if info.get("trailingPE") else None,
        "pb_ratio": round(info["priceToBook"], 2) if info.get("priceToBook") else None,
        "dividend_yield": round(info["dividendYield"], 2) if info.get("dividendYield") else None,
        "eps": round(info["trailingEps"], 2) if info.get("trailingEps") else None,
        "week52_high": round(info["fiftyTwoWeekHigh"], 2) if info.get("fiftyTwoWeekHigh") else None,
        "week52_low": round(info["fiftyTwoWeekLow"], 2) if info.get("fiftyTwoWeekLow") else None,
        "analyst_target": round(info["targetMeanPrice"], 2) if info.get("targetMeanPrice") else None,
        "analyst_count": info.get("numberOfAnalystOpinions"),
    }


def _levels(prices: list, volumes: list) -> list:
    out = []
    for p, v in zip(prices, volumes):
        if p == "-" or v == "-":
            continue
        out.append({"price": round(float(p), 2), "volume": int(v)})
    return out


@ttl_cache(seconds=30)
def fetch_orderbook(ticker: str) -> dict:
    """五檔報價：twstock.realtime 直接拿 TWSE/TPEx 的即時委買委賣，免金鑰。
    盤前/盤後可能沒有掛單，回傳的某幾檔會是 "-"，這裡濾掉。
    """
    quote = twstock.realtime.get(ticker)
    if not quote.get("success"):
        return {"error": f"No realtime quote for {ticker}"}

    rt = quote["realtime"]
    return {
        "asks": _levels(rt["best_ask_price"], rt["best_ask_volume"]),
        "bids": _levels(rt["best_bid_price"], rt["best_bid_volume"]),
    }
