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


def _render(rows: list[dict]) -> dict:
    """row dicts → API 回傳 JSON。四捨五入到 2 位在這裡做（與舊行為一致）。"""
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
    prev_price = rows[-2]["close"] if len(rows) >= 2 else rows[-1]["close"]
    limit_up, limit_down = _limit_prices(prev_price)
    return {
        "candles": candles,
        "volume": volume,
        "limit_up": limit_up,
        "limit_down": limit_down,
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

    need_front_fill = (
        cov is not None
        and start_str is not None
        and start_str < cov[0]
        and not _front_fill_impossible(yft, interval, cov[0])
    )

    if cov is None or start_str is None or need_front_fill:
        # 全抓：庫是空的／要的區間比庫存更早／period=max。直接回抓到的內容
        # （跟改動前的行為逐 byte 一致），寫入 SQLite 是順手的副作用。
        rows = _yf_rows(ticker, interval, False, period=period)
        if not rows:
            return {"error": f"No data found for {ticker}.TW"}
        store.upsert(yft, interval, rows)
        _maybe_record_source_start(yft, interval, period, cutoff, rows[0]["time"])
        logger.info("%s %s %s: 全抓 %d 根（%s）", yft, interval, period, len(rows),
                    "庫空" if cov is None else "要補更早區間" if need_front_fill else "period=max")
        return _render(rows)

    # 增量：從庫存倒數第 TAIL_OVERLAP 根抓起（故意重疊，用來偵測除權息）
    overlap_start = store.tail_ts(yft, interval, TAIL_OVERLAP)
    new_rows = _yf_rows(ticker, interval, False, start=overlap_start)

    if not new_rows:
        # 外部來源暫時抓不到 → 歷史 K 線用庫存頂上（歷史不會過期），記一筆警告
        rows = store.rows_since(yft, interval, start_str)
        if not rows:
            return {"error": f"No data found for {ticker}.TW"}
        logger.warning("%s %s: yfinance 回空，以庫存 %d 根回應", yft, interval, len(rows))
        return _render(rows)

    stored_closes = store.closes_since(yft, interval, overlap_start)
    adjusted = any(
        r["time"] in stored_closes
        and stored_closes[r["time"]] != 0
        and abs(r["close"] / stored_closes[r["time"]] - 1) > ADJUST_TOLERANCE
        for r in new_rows
    )
    if adjusted:
        # 除權息：還原價整條平移了，庫存跟新資料對不上 → 已存區間整段重抓覆寫
        logger.info("%s %s: 重疊處 close 對不上（除權息還原），整段重抓", yft, interval)
        full_rows = _yf_rows(ticker, interval, False, start=cov[0])
        if full_rows:
            store.upsert(yft, interval, full_rows)
    else:
        store.upsert(yft, interval, new_rows)

    rows = store.rows_since(yft, interval, start_str)
    if not rows:
        return {"error": f"No data found for {ticker}.TW"}
    logger.info("%s %s %s: 庫存命中，向 yfinance 只要了 %d 根，回 %d 根",
                yft, interval, period, len(new_rows), len(rows))
    return _render(rows)


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
    return _render(rows)


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
        "market_cap": round(market_cap / 1e8, 1) if market_cap else 0,
        "shares_outstanding": round(shares / 1e8, 2) if shares else 0,
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
