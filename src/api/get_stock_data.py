#!/usr/bin/env python3
"""技術指標計算佔位層（TEMP）。

這支腳本站在「後端」的暫時替身位置：raw K 線改跟中台（data_service/）要，這裡只算
SMA/RSI/MACD/K線型態(mock)/latest metrics——這些「計算」本來就該是後端的工作，但隊友
的後端還在另一條 branch 開發，還沒 merge 回 main。等 merge 完成，
frontend/src/app/api/stock/[ticker]/route.ts 要改成直接打隊友後端的 API，
這支腳本要整支刪除；data_service/ 不受影響（JSON 形狀＝合約，見 docs/thinking.md 十四）。

Usage: python3 get_stock_data.py <ticker> [period] [interval]
  ticker:   Taiwan stock code without .TW suffix (e.g. 2330)
  period:   yfinance period string (1mo | 3mo | 6mo | 1y | 2y | 5y | 10y | max), default 6mo
  interval: yfinance interval string (5m | 15m | 30m | 60m | 1d | 1wk | 1mo), default 1d
"""
import json
import os
import sys
import urllib.request

import pandas as pd
import twstock

DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://localhost:8001")


def _company_name(ticker: str) -> str:
    info = twstock.codes.get(ticker)
    return info.name if info else ticker


def _fetch_candles(ticker: str, period: str, interval: str) -> dict:
    url = f"{DATA_SERVICE_URL}/stocks/{ticker}/candles?period={period}&interval={interval}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


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


def _to_tv(series: pd.Series, times: list) -> list:
    """Convert pandas Series (index-aligned with `times`) → [{"time": ..., "value": float}]"""
    out = []
    for t, val in zip(times, series):
        if pd.isna(val):
            continue
        out.append({"time": t, "value": round(float(val), 4)})
    return out


# mock：K 線型態辨識（晨星、錘子線、吞噬等）。TA-Lib 的 61 種型態（pattern.py，Phase 2）
# 還沒接進這支 script（執行環境沒裝 TA-Lib C 函式庫），先固定回傳近期幾筆假資料占位。
def _mock_patterns(candles: list) -> list:
    if len(candles) < 5:
        return []
    sample = candles[-5]
    return [{"time": sample["time"], "name": "錘子線", "signal": "bullish"}]


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"
    period = sys.argv[2] if len(sys.argv) > 2 else "6mo"
    interval = sys.argv[3] if len(sys.argv) > 3 else "1d"

    raw = _fetch_candles(ticker, period, interval)
    if "error" in raw:
        print(json.dumps({"error": raw["error"]}))
        sys.exit(1)

    candles = raw["candles"]
    volume_data = raw["volume"]
    times = [c["time"] for c in candles]

    close = pd.Series([c["close"] for c in candles])
    volume = pd.Series([v["value"] for v in volume_data])

    sma20 = close.rolling(20).mean()
    sma60 = close.rolling(60).mean()
    rsi_vals = _rsi(close)
    macd_line, macd_signal, macd_hist = _macd(close)

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
        "sma20": _to_tv(sma20, times),
        "sma60": _to_tv(sma60, times),
        "rsi": _to_tv(rsi_vals, times),
        "macd": {
            "line": _to_tv(macd_line, times),
            "signal": _to_tv(macd_signal, times),
            "histogram": _to_tv(macd_hist, times),
        },
        "patterns": _mock_patterns(candles),
        "latest": {
            "price": round(latest_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "rsi": round(latest_rsi, 1),
            "macd_crossover": "golden" if latest_macd > latest_sig else "dead",
            "volume_ratio": round(vol_ratio, 2),
            "limit_up": raw["limit_up"],
            "limit_down": raw["limit_down"],
        },
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
