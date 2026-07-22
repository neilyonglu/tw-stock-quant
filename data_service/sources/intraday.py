"""今日分時走勢（1 分鐘間隔），個股和大盤共用。搬自舊 src/api/get_intraday.py。"""
import calendar

import yfinance as yf

from data_service.cache import ttl_cache


@ttl_cache(seconds=30)
def fetch_intraday(symbol: str) -> dict:
    """symbol：完整 yfinance 代碼，個股傳 "2330.TW"，大盤傳 "^TWII"。"""
    ticker = yf.Ticker(symbol)
    intraday = ticker.history(period="1d", interval="1m").dropna(subset=["Close", "Volume"])
    if intraday.empty:
        return {"error": f"No intraday data for {symbol}"}

    daily = ticker.history(period="5d", interval="1d").dropna(subset=["Close"])
    prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else float(intraday["Close"].iloc[0])

    cum_pv = 0.0  # price * volume 累計，算累計均價線
    cum_vol = 0.0
    points = []
    for ts, row in intraday.iterrows():
        price = float(row["Close"])
        vol = float(row["Volume"])
        cum_pv += price * vol
        cum_vol += vol
        avg_price = (cum_pv / cum_vol) if cum_vol > 0 else price
        points.append({
            # lightweight-charts 軸籤一律按 UTC 顯示，這裡把台北壁鐘時間直接當 UTC
            # 算 epoch，圖表才會顯示台北的盤中時間（跟 stock.py 的「假 UTC」技巧一樣）。
            "time": calendar.timegm(ts.timetuple()),
            "price": round(price, 2),
            "avg_price": round(avg_price, 2),
            "volume": vol,
        })

    return {"prev_close": round(prev_close, 2), "points": points}
