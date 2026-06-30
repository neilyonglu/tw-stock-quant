#!/usr/bin/env python3
"""
抓今日分時走勢（1 分鐘間隔），個股和大盤共用，來自 yfinance，免金鑰。
對應 frontend IntradaySeries（lib/types.ts）。
Usage: python3 get_intraday.py <yfinance_symbol>
  symbol: 完整 yfinance 代碼，個股傳 "2330.TW"，大盤傳 "^TWII"
"""
import calendar
import json
import sys

import yfinance as yf


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "2330.TW"

    ticker = yf.Ticker(symbol)
    intraday = ticker.history(period="1d", interval="1m").dropna(subset=["Close", "Volume"])
    if intraday.empty:
        print(json.dumps({"error": f"No intraday data for {symbol}"}))
        sys.exit(1)

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
            # 跟 get_stock_data.py 的「假 UTC」技巧一樣：lightweight-charts 軸籤一律按 UTC
            # 顯示，這裡把台北壁鐘時間直接當 UTC 算 epoch，圖表才會顯示台北的盤中時間。
            "time": calendar.timegm(ts.timetuple()),
            "price": round(price, 2),
            "avg_price": round(avg_price, 2),
            "volume": vol,
        })

    print(json.dumps({"prev_close": round(prev_close, 2), "points": points}))


if __name__ == "__main__":
    main()
