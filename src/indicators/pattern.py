"""K 線型態辨識（TA-Lib）。

只接選股規則（plan.md 第四層）用到的型態，多空各三種。TA-Lib 的 CDL* 函式回傳
+100（偏多）/ -100（偏空）/ 0（無），吞噬同一個函式兩種方向都會回。
"""

from typing import TypedDict

import numpy as np
import pandas as pd
import talib


class Pattern(TypedDict):
    time: str | int
    name: str
    signal: str  # "bullish" | "bearish"


# (TA-Lib 函式, 偏多名稱, 偏空名稱)；單向型態另一側填 None
_PATTERNS: list[tuple[str, str | None, str | None]] = [
    ("CDLMORNINGSTAR", "晨星", None),
    ("CDLEVENINGSTAR", None, "黃昏星"),
    ("CDLHAMMER", "錘子線", None),
    ("CDLHANGINGMAN", None, "上吊線"),
    ("CDLENGULFING", "多頭吞噬", "空頭吞噬"),
]


def detect_patterns(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    times: list,
    recent: int = 5,
) -> list[Pattern]:
    """回傳最近 `recent` 根 K 棒內出現的型態，依時間排序。

    只看最近幾根：型態是「此刻」的訊號，六個月前的錘子線對現在沒有意義，
    而且呼叫端會把每筆都當成一個訊號徽章顯示。
    """
    if len(close) < 2:
        return []
    arrays = [s.to_numpy(dtype=np.float64) for s in (open_, high, low, close)]
    start = max(0, len(close) - recent)
    found: list[Pattern] = []
    for fn_name, bull, bear in _PATTERNS:
        flags = getattr(talib, fn_name)(*arrays)
        for i in range(start, len(close)):
            if flags[i] > 0 and bull:
                found.append({"time": times[i], "name": bull, "signal": "bullish"})
            elif flags[i] < 0 and bear:
                found.append({"time": times[i], "name": bear, "signal": "bearish"})
    found.sort(key=lambda p: times.index(p["time"]))
    return found
