"""動能類指標：RSI / KD。"""

import pandas as pd


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """RSI，用 Wilder's smoothing（TA-Lib、TradingView、券商看盤軟體的標準算法）。

    種子＝前 window 根漲跌幅的簡單平均，之後遞迴平滑（等價於 alpha=1/window 的 EMA）。
    用簡單移動平均算出來的數字會跟看盤軟體差 2～5，使用者對照時會以為系統算錯。
    資料不足一個 window 時整段回 NaN，由呼叫端決定怎麼呈現。
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = pd.Series(index=close.index, dtype="float64")
    avg_loss = pd.Series(index=close.index, dtype="float64")
    if len(close) <= window:
        return avg_gain

    avg_gain.iloc[window] = gain.iloc[1 : window + 1].mean()
    avg_loss.iloc[window] = loss.iloc[1 : window + 1].mean()
    for i in range(window + 1, len(close)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (window - 1) + gain.iloc[i]) / window
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (window - 1) + loss.iloc[i]) / window

    rs = avg_gain / avg_loss
    # 全段沒下跌時 avg_loss=0 → rs=inf → RSI=100，是定義上的正確值
    return 100 - 100 / (1 + rs)


def kd(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 9,
) -> tuple[pd.Series, pd.Series]:
    """台股版 KD（9,3,3）：K = ⅔×前K + ⅓×RSV，D = ⅔×前D + ⅓×K，起始值 50。

    跟 TA-Lib 的 STOCH 不同——後者預設 (5,3,3) 且用簡單平均平滑，算出來會跟台灣券商
    看盤軟體差好幾點。這裡刻意照台灣慣例寫，讓使用者對照券商 App 時數字一致。
    前 window-1 根沒有完整區間，回 NaN。
    """
    lowest = low.rolling(window).min()
    highest = high.rolling(window).max()
    span = highest - lowest
    # 區間內最高＝最低（連續漲停/跌停鎖死）時 RSV 無定義，慣例當 50（中性）；
    # 用 != 0 而不是 > 0，前 window-1 根 span 是 NaN 要保留 NaN、不能誤填 50
    rsv = ((close - lowest) / span * 100).where(span != 0, 50.0)

    k = pd.Series(index=close.index, dtype="float64")
    d = pd.Series(index=close.index, dtype="float64")
    prev_k = prev_d = 50.0
    for i in range(len(close)):
        if pd.isna(rsv.iloc[i]):
            continue
        prev_k = prev_k * 2 / 3 + rsv.iloc[i] / 3
        prev_d = prev_d * 2 / 3 + prev_k / 3
        k.iloc[i] = prev_k
        d.iloc[i] = prev_d
    return k, d
