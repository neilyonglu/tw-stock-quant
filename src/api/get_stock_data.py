#!/usr/bin/env python3
"""
Fetch OHLCV + technical indicators for a Taiwan stock via yfinance.
Prints JSON to stdout.
Usage: python3 get_stock_data.py <ticker> [period] [interval]
  ticker:   Taiwan stock code without .TW suffix (e.g. 2330)
  period:   yfinance period string (1mo | 3mo | 6mo | 1y | 2y | 5y | 10y | max), default 6mo
  interval: yfinance interval string (5m | 15m | 30m | 60m | 1d | 1wk | 1mo), default 1d
"""
import calendar
import json
import sys

import pandas as pd
import twstock
import yfinance as yf

INTRADAY_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}

# 台股慣例：紅漲綠跌（跟美股的 green-up / red-down 相反）
STOCK_UP = "#EF5350"  # 漲：紅
STOCK_DOWN = "#26A69A"  # 跌：綠


def _company_name(ticker: str) -> str:
    info = twstock.codes.get(ticker)
    return info.name if info else ticker


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)


def _macd(close: pd.Series):
    fast = _ema(close, 12)
    slow = _ema(close, 26)
    line = fast - slow
    signal = _ema(line, 9)
    hist = line - signal
    return line, signal, hist


def _fmt_time(ts, is_intraday: bool):
    """Intraday → unix timestamp (秒，圖表才能畫出時分); 日/週/月 → "YYYY-MM-DD"。

    lightweight-charts 一律用 UTC 解讀並顯示 timestamp 軸籤，跟瀏覽器所在時區無關。
    若直接轉真正的 UTC epoch，台股 09:00 開盤會被顯示成 01:00。這裡改用「假 UTC」：
    把台北本地的時、分數字直接當成 UTC 算 epoch，圖表上才會顯示台北的盤中時間。
    """
    if is_intraday:
        return calendar.timegm(ts.timetuple())
    return ts.strftime("%Y-%m-%d")


def _to_tv(series: pd.Series, is_intraday: bool) -> list:
    """Convert pandas Series → [{"time": ..., "value": float}]"""
    out = []
    for ts, val in series.dropna().items():
        out.append({"time": _fmt_time(ts, is_intraday), "value": round(float(val), 4)})
    return out


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"
    period = sys.argv[2] if len(sys.argv) > 2 else "6mo"
    interval = sys.argv[3] if len(sys.argv) > 3 else "1d"
    is_intraday = interval in INTRADAY_INTERVALS

    df = yf.Ticker(f"{ticker}.TW").history(period=period, interval=interval)
    if df.empty:
        print(json.dumps({"error": f"No data found for {ticker}.TW"}))
        sys.exit(1)

    close = df["Close"]
    volume = df["Volume"]

    sma20 = close.rolling(20).mean()
    sma60 = close.rolling(60).mean()
    rsi_vals = _rsi(close)
    macd_line, macd_signal, macd_hist = _macd(close)

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

    volume_data = [
        {
            "time": _fmt_time(idx, is_intraday),
            "value": float(r["Volume"]),
            "color": STOCK_UP if r["Close"] >= r["Open"] else STOCK_DOWN,
        }
        for idx, r in df.iterrows()
    ]

    latest_price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2])
    change = latest_price - prev_price
    change_pct = change / prev_price * 100
    latest_rsi = float(rsi_vals.dropna().iloc[-1])
    latest_macd = float(macd_line.dropna().iloc[-1])
    latest_sig = float(macd_signal.dropna().iloc[-1])
    vol_avg5 = float(volume.iloc[-6:-1].mean()) if len(volume) >= 6 else float(volume.mean())
    vol_ratio = float(volume.iloc[-1]) / vol_avg5 if vol_avg5 > 0 else 1.0

    result = {
        "ticker": ticker,
        "name": _company_name(ticker),
        "candles": candles,
        "volume": volume_data,
        "sma20": _to_tv(sma20, is_intraday),
        "sma60": _to_tv(sma60, is_intraday),
        "rsi": _to_tv(rsi_vals, is_intraday),
        "macd": {
            "line": _to_tv(macd_line, is_intraday),
            "signal": _to_tv(macd_signal, is_intraday),
            "histogram": _to_tv(macd_hist, is_intraday),
        },
        "latest": {
            "price": round(latest_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "rsi": round(latest_rsi, 1),
            "macd_crossover": "golden" if latest_macd > latest_sig else "dead",
            "volume_ratio": round(vol_ratio, 2),
        },
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
