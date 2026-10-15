"""技術指標計算層。

輸入是中台回的 raw OHLCV DataFrame（欄位 open/high/low/close/volume），
`add_indicators` 把所有指標加成新欄位回傳；個別函式也可單獨呼叫。
"""

import pandas as pd

from .momentum import kd, rsi
from .pattern import detect_patterns
from .trend import ema, macd, sma
from .volatility import atr
from .volume import volume_ratio, volume_sma

__all__ = [
    "add_indicators",
    "atr",
    "detect_patterns",
    "ema",
    "kd",
    "macd",
    "rsi",
    "sma",
    "volume_ratio",
    "volume_sma",
]


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """回傳加上指標欄位的新 DataFrame（不改動輸入）。

    新增欄位：sma20, sma60, rsi14, macd, macd_signal, macd_hist, k, d, atr14,
    volume_sma5, volume_sma10。資料不足的位置為 NaN。
    """
    out = df.copy()
    out["sma20"] = sma(df["close"], 20)
    out["sma60"] = sma(df["close"], 60)
    out["rsi14"] = rsi(df["close"], 14)
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(df["close"])
    out["k"], out["d"] = kd(df["high"], df["low"], df["close"])
    out["atr14"] = atr(df["high"], df["low"], df["close"], 14)
    out["volume_sma5"] = volume_sma(df["volume"], 5)
    out["volume_sma10"] = volume_sma(df["volume"], 10)
    return out
