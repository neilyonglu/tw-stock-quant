#!/usr/bin/env python3
"""技術指標計算佔位層（TEMP）。

這支腳本站在「後端」的暫時替身位置：raw K 線改跟中台（data_service/）要，這裡只算
SMA/RSI/MACD/K線型態(mock)/latest metrics——這些「計算」本來就該是後端的工作，但隊友
的後端還在另一條 branch 開發，還沒 merge 回 main。等 merge 完成，
frontend/src/app/api/stock/[ticker]/route.ts 要改成直接打隊友後端的 API，
這支腳本要整支刪除；data_service/ 不受影響（JSON 形狀＝合約，見 PROJECT.md「API 合約原則」）。

Usage: python3 get_stock_data.py <ticker> [period] [interval]
  ticker:   Taiwan stock code without .TW suffix (e.g. 2330)
  period:   yfinance period string (1mo | 3mo | 6mo | 1y | 2y | 5y | 10y | max), default 6mo
  interval: yfinance interval string (5m | 15m | 30m | 60m | 1d | 1wk | 1mo), default 1d
"""
import json
import os
import sys
import urllib.error
import urllib.request

import pandas as pd
import twstock

DATA_SERVICE_URL = os.environ.get("DATA_SERVICE_URL", "http://localhost:8001")


def _company_name(ticker: str) -> str:
    info = twstock.codes.get(ticker)
    return info.name if info else ticker


def _fetch_candles(ticker: str, period: str, interval: str) -> dict:
    url = f"{DATA_SERVICE_URL}/stocks/{ticker}/candles?period={period}&interval={interval}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        # 中台查無此股票代碼會回 404，這裡沒接住的話會整支腳本炸掉、前端只看得到
        # 「Failed to fetch stock data」這種沒意義的訊息，接住改成使用者看得懂的提示。
        if e.code == 404:
            return {"error": f"查無股票代碼「{ticker}」，請確認代碼是否正確"}
        raise


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """RSI，用 Wilder's smoothing（TA-Lib、TradingView、券商看盤軟體的標準算法）。

    Wilder 的平滑等價於 alpha = 1/window 的指數移動平均，pandas 用
    `ewm(alpha=1/window, adjust=False)` 表達；前 window 根用簡單平均當種子。
    原本用 `rolling(window).mean()`（簡單移動平均）算出來的數字會跟 TradingView
    差 2～5，使用者拿去對照會以為系統算錯。
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = pd.Series(index=close.index, dtype="float64")
    avg_loss = pd.Series(index=close.index, dtype="float64")
    if len(close) <= window:
        return avg_gain  # 資料不足一個 window，整段 NaN（呼叫端已處理）

    # 種子＝前 window 根漲跌幅的簡單平均；之後才進入 Wilder 遞迴平滑
    avg_gain.iloc[window] = gain.iloc[1 : window + 1].mean()
    avg_loss.iloc[window] = loss.iloc[1 : window + 1].mean()
    for i in range(window + 1, len(close)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (window - 1) + gain.iloc[i]) / window
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (window - 1) + loss.iloc[i]) / window

    rs = avg_gain / avg_loss
    # 全段都沒下跌時 avg_loss=0 → rs=inf → RSI=100，這是定義上的正確值，不是錯誤
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


def _patterns(candles: list) -> list:
    """K 線型態辨識（晨星、錘子線、吞噬等），尚未實作。

    這裡刻意回傳空陣列。原本會固定塞一筆「錘子線 / bullish」假資料佔位，但前端把它
    跟真的 SMA/MACD/RSI 訊號並排顯示、外觀完全一樣，等於每次開個股頁都餵給使用者
    一個假的多頭訊號——在會影響真實投資決策的系統裡這是安全問題，不是佔位方便性問題。
    寧可空白，也不要一個看起來合理的假訊號。

    要接真的：TA-Lib 有 61 種型態辨識，但這支腳本跑的 python 環境沒裝 TA-Lib
    C 函式庫（見 PROJECT.md「兩個 Python 環境」），指標層扶正時一起解決。
    """
    return []


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"
    period = sys.argv[2] if len(sys.argv) > 2 else "6mo"
    interval = sys.argv[3] if len(sys.argv) > 3 else "1d"

    raw = _fetch_candles(ticker, period, interval)
    if "error" in raw:
        # exit(0)：這是已知、處理過的錯誤（查無代碼），不是腳本壞掉。exit(1) 會讓
        # Node 的 execFile 把 stdout 整包丟掉（見 run-python.ts），前端就看不到這則
        # 錯誤訊息，只會拿到通用的「Failed to fetch stock data」。
        print(json.dumps({"error": raw["error"]}))
        sys.exit(0)

    candles = raw["candles"]
    volume_data = raw["volume"]
    times = [c["time"] for c in candles]

    close = pd.Series([c["close"] for c in candles])
    volume = pd.Series([v["value"] for v in volume_data])

    sma20 = close.rolling(20).mean()
    sma60 = close.rolling(60).mean()
    rsi_vals = _rsi(close)
    macd_line, macd_signal, macd_hist = _macd(close)
    volume_sma5 = volume.rolling(5).mean()
    volume_sma10 = volume.rolling(10).mean()

    latest_price = float(close.iloc[-1])
    # 只有 1 根 K 棒時（新股上市首日、極短區間）沒有前一根可比，漲跌當 0，
    # 不要 close.iloc[-2] 直接 IndexError 炸掉整支腳本。
    prev_price = float(close.iloc[-2]) if len(close) >= 2 else latest_price
    change = latest_price - prev_price
    change_pct = (change / prev_price * 100) if prev_price else 0.0
    rsi_dropna = rsi_vals.dropna()
    # 資料筆數不夠一個 RSI window（14）時會全 NaN——「今日」這種短區間會踩到，
    # 用 50（中性值）佔位，避免整支腳本炸掉；比空白 UI 誠實一點，不是真訊號但不會誤判超買超賣。
    latest_rsi = float(rsi_dropna.iloc[-1]) if len(rsi_dropna) > 0 else 50.0
    macd_dropna = macd_line.dropna()
    sig_dropna = macd_signal.dropna()
    # 同理：資料太短時 MACD/訊號線也可能全 NaN，兩邊都取不到就當 0（金叉死叉判定為死叉）
    latest_macd = float(macd_dropna.iloc[-1]) if len(macd_dropna) > 0 else 0.0
    latest_sig = float(sig_dropna.iloc[-1]) if len(sig_dropna) > 0 else 0.0
    vol_avg5 = float(volume.iloc[-6:-1].mean()) if len(volume) >= 6 else float(volume.mean())
    vol_ratio = float(volume.iloc[-1]) / vol_avg5 if vol_avg5 > 0 else 1.0

    result = {
        "ticker": ticker,
        "name": _company_name(ticker),
        "candles": candles,
        "volume": volume_data,
        "sma20": _to_tv(sma20, times),
        "sma60": _to_tv(sma60, times),
        "volume_sma5": _to_tv(volume_sma5, times),
        "volume_sma10": _to_tv(volume_sma10, times),
        "rsi": _to_tv(rsi_vals, times),
        "macd": {
            "line": _to_tv(macd_line, times),
            "signal": _to_tv(macd_signal, times),
            "histogram": _to_tv(macd_hist, times),
        },
        "patterns": _patterns(candles),
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
