"""波動類指標：ATR。"""

import pandas as pd


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(
        axis=1
    )


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """ATR，Wilder's smoothing（與 TA-Lib 一致）。

    第一根 TR 沒有前收盤，只能用 high-low；種子＝第 1..window 根 TR 的簡單平均，之後遞迴平滑。
    資料不足 window+1 根時整段回 NaN。
    """
    tr = true_range(high, low, close)
    tr.iloc[0] = high.iloc[0] - low.iloc[0]

    out = pd.Series(index=close.index, dtype="float64")
    if len(close) <= window:
        return out
    out.iloc[window] = tr.iloc[1 : window + 1].mean()
    for i in range(window + 1, len(close)):
        out.iloc[i] = (out.iloc[i - 1] * (window - 1) + tr.iloc[i]) / window
    return out
