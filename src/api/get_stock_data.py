"""個股頁面資料組裝：跟中台要 raw K 線 → src.indicators 算指標 → 輸出前端合約 JSON。

由 frontend/src/lib/run-python.ts 以模組方式執行（`uv run python -m src.api.get_stock_data`），
輸出形狀＝frontend/src/lib/types.ts 的 `StockData`，改欄位前要先對齊那邊。

Usage: python -m src.api.get_stock_data <ticker> [period] [interval]
  ticker:   台股代碼，不含 .TW（例 2330）
  period:   yfinance period（1mo | 3mo | 6mo | 1y | 2y | 5y | 10y | max），預設 6mo
  interval: yfinance interval（5m | 15m | 30m | 60m | 1d | 1wk | 1mo），預設 1d
"""

import json
import os
import sys
import urllib.error
import urllib.request

import pandas as pd
import twstock

from src.indicators import add_indicators, detect_patterns, volume_ratio

DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://localhost:8001")


def _company_name(ticker: str) -> str:
    info = twstock.codes.get(ticker)
    return info.name if info else ticker


def _fetch_candles(ticker: str, period: str, interval: str) -> dict:
    url = f"{DATA_SERVICE_URL}/stocks/{ticker}/candles?period={period}&interval={interval}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data: dict = json.load(resp)
            return data
    except urllib.error.HTTPError as e:
        # 中台查無此股票代碼會回 404，不接住的話前端只看得到「Failed to fetch stock data」
        if e.code == 404:
            return {"error": f"查無股票代碼「{ticker}」，請確認代碼是否正確"}
        raise


def _to_tv(series: pd.Series, times: list) -> list:
    """pandas Series（與 times 對齊）→ lightweight-charts 的 [{"time", "value"}]，略過 NaN。"""
    return [
        {"time": t, "value": round(float(v), 4)}
        for t, v in zip(times, series, strict=True)
        if not pd.isna(v)
    ]


def _last_or(series: pd.Series, default: float) -> float:
    """最後一個非 NaN 值；資料太短整段 NaN 時（例如「今日」5 分線不足 14 根）回預設值。"""
    valid = series.dropna()
    return float(valid.iloc[-1]) if len(valid) > 0 else default


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"
    period = sys.argv[2] if len(sys.argv) > 2 else "6mo"
    interval = sys.argv[3] if len(sys.argv) > 3 else "1d"

    raw = _fetch_candles(ticker, period, interval)
    if "error" in raw:
        # exit(0)：查無代碼是已處理的已知狀況，exit(1) 會讓 execFile 丟掉 stdout
        print(json.dumps({"error": raw["error"]}))
        sys.exit(0)

    candles = raw["candles"]
    volume_data = raw["volume"]
    times = [c["time"] for c in candles]

    df = pd.DataFrame(
        {
            "open": [c["open"] for c in candles],
            "high": [c["high"] for c in candles],
            "low": [c["low"] for c in candles],
            "close": [c["close"] for c in candles],
            "volume": [v["value"] for v in volume_data],
        }
    )
    ind = add_indicators(df)

    latest_price = float(df["close"].iloc[-1])
    # 只有 1 根 K 棒時沒有前一根可比，漲跌當 0
    prev_price = float(df["close"].iloc[-2]) if len(df) >= 2 else latest_price
    change = latest_price - prev_price
    change_pct = (change / prev_price * 100) if prev_price else 0.0

    # RSI 不足一個 window 用 50（中性）佔位；MACD 取不到當 0（判成死叉），都不會誤判超買超賣
    latest_rsi = _last_or(ind["rsi14"], 50.0)
    latest_macd = _last_or(ind["macd"], 0.0)
    latest_sig = _last_or(ind["macd_signal"], 0.0)

    result = {
        "ticker": ticker,
        "name": _company_name(ticker),
        "candles": candles,
        "volume": volume_data,
        "sma20": _to_tv(ind["sma20"], times),
        "sma60": _to_tv(ind["sma60"], times),
        "volume_sma5": _to_tv(ind["volume_sma5"], times),
        "volume_sma10": _to_tv(ind["volume_sma10"], times),
        "rsi": _to_tv(ind["rsi14"], times),
        "macd": {
            "line": _to_tv(ind["macd"], times),
            "signal": _to_tv(ind["macd_signal"], times),
            "histogram": _to_tv(ind["macd_hist"], times),
        },
        "patterns": detect_patterns(df["open"], df["high"], df["low"], df["close"], times),
        "latest": {
            "price": round(latest_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "rsi": round(latest_rsi, 1),
            "macd_crossover": "golden" if latest_macd > latest_sig else "dead",
            "volume_ratio": round(volume_ratio(df["volume"]), 2),
            "limit_up": raw["limit_up"],
            "limit_down": raw["limit_down"],
        },
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
