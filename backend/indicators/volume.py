"""量能類指標：均量線 / 量比。"""

import pandas as pd


def volume_sma(volume: pd.Series, window: int) -> pd.Series:
    return volume.rolling(window).mean()


def volume_ratio(volume: pd.Series, window: int = 5) -> float:
    """最新一根成交量 ÷ 前 window 根平均量（不含最新那根）。

    資料不足時退回全段平均；平均為 0（停牌）時回 1.0 當中性值。
    """
    if len(volume) == 0:
        return 1.0
    if len(volume) > window:
        avg = float(volume.iloc[-window - 1 : -1].mean())
    else:
        avg = float(volume.mean())
    return float(volume.iloc[-1]) / avg if avg > 0 else 1.0
