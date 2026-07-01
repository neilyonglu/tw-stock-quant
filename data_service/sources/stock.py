"""個股 raw 資料：K 線/成交量/基本面/五檔。只做「抓取」，不算 SMA/RSI/MACD 等指標
（那些是後端該做的計算，見 docs/thinking.md 2026-07-01 中台拆分說明）。
搬自舊 src/api/{get_stock_data,get_stock_profile,get_orderbook}.py。
"""
import calendar

import twstock
import yfinance as yf

from data_service.cache import ttl_cache

INTRADAY_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}

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


@ttl_cache(seconds=60)
def fetch_candles(ticker: str, period: str, interval: str) -> dict:
    """raw OHLCV + 成交量 + 漲跌停價，不含任何技術指標。"""
    is_intraday = interval in INTRADAY_INTERVALS

    df = yf.Ticker(f"{ticker}.TW").history(period=period, interval=interval)
    # 交易日當天還沒收盤時，yfinance 會多回傳一筆 OHLC 全是 NaN 的列，留著會讓
    # json.dumps 印出裸 NaN token，前端 JSON.parse 直接炸掉。
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        return {"error": f"No data found for {ticker}.TW"}

    close = df["Close"]
    candles = [
        {
            "time": _fmt_time(idx, is_intraday),
            "open": round(float(r["Open"]), 2),
            "high": round(float(r["High"]), 2),
            "low": round(float(r["Low"]), 2),
            "close": round(float(r["Close"]), 2),
        }
        for idx, r in df.iterrows()
    ]
    volume = [
        {
            "time": _fmt_time(idx, is_intraday),
            "value": float(r["Volume"]),
            "color": STOCK_UP if r["Close"] >= r["Open"] else STOCK_DOWN,
        }
        for idx, r in df.iterrows()
    ]

    prev_price = float(close.iloc[-2]) if len(close) >= 2 else float(close.iloc[-1])
    limit_up, limit_down = _limit_prices(prev_price)

    return {
        "candles": candles,
        "volume": volume,
        "limit_up": limit_up,
        "limit_down": limit_down,
    }


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
