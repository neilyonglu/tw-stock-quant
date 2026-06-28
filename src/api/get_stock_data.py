#!/usr/bin/env python3
"""
Fetch OHLCV + technical indicators for a Taiwan stock via yfinance.
Prints JSON to stdout.
Usage: python3 get_stock_data.py <ticker> [period]
  ticker: Taiwan stock code without .TW suffix (e.g. 2330)
  period: yfinance period string (1mo | 3mo | 6mo | 1y), default 6mo
"""
import sys
import json
import pandas as pd
import yfinance as yf


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


def _to_tv(series: pd.Series) -> list:
    """Convert pandas Series → [{"time": "YYYY-MM-DD", "value": float}]"""
    out = []
    for ts, val in series.dropna().items():
        out.append({"time": ts.strftime("%Y-%m-%d"), "value": round(float(val), 4)})
    return out


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"
    period = sys.argv[2] if len(sys.argv) > 2 else "6mo"

    df = yf.Ticker(f"{ticker}.TW").history(period=period)
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
            "time": idx.strftime("%Y-%m-%d"),
            "open": round(float(r["Open"]), 2),
            "high": round(float(r["High"]), 2),
            "low": round(float(r["Low"]), 2),
            "close": round(float(r["Close"]), 2),
        }
        for idx, r in df.iterrows()
    ]

    volume_data = [
        {
            "time": idx.strftime("%Y-%m-%d"),
            "value": float(r["Volume"]),
            "color": "#26A69A" if r["Close"] >= r["Open"] else "#EF5350",
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
        "candles": candles,
        "volume": volume_data,
        "sma20": _to_tv(sma20),
        "sma60": _to_tv(sma60),
        "rsi": _to_tv(rsi_vals),
        "macd": {
            "line": _to_tv(macd_line),
            "signal": _to_tv(macd_signal),
            "histogram": _to_tv(macd_hist),
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
