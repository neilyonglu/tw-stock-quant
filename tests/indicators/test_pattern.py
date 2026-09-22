import pandas as pd

from src.indicators.pattern import detect_patterns


def _bars(rows: list[tuple[float, float, float, float]]) -> dict[str, pd.Series]:
    cols = [pd.Series(col) for col in zip(*rows, strict=True)]
    return dict(zip(("open_", "high", "low", "close"), cols, strict=True))


# 前面墊幾根小實體 K 棒，再放一根紅 K 接一根完全包住它的綠 K → 多頭吞噬
_ENGULFING_ROWS = [
    (100.0, 101.0, 99.0, 100.5),
    (100.5, 101.5, 99.5, 100.0),
    (100.0, 101.0, 99.0, 100.5),
    (100.0, 100.5, 94.5, 95.0),  # 紅 K：開 100 收 95
    (94.0, 102.0, 93.5, 101.0),  # 綠 K：開 94 收 101，包住前一根實體
]


def test_bullish_engulfing_detected():
    bars = _bars(_ENGULFING_ROWS)
    times = list(range(len(_ENGULFING_ROWS)))
    found = detect_patterns(**bars, times=times)
    assert {"time": 4, "name": "多頭吞噬", "signal": "bullish"} in found


def test_only_recent_bars_are_reported():
    # 吞噬之後再墊 5 根平淡 K 棒，型態落在 recent=5 視窗外 → 不回報
    rows = _ENGULFING_ROWS + [(101.0, 101.5, 100.5, 101.0)] * 5
    bars = _bars(rows)
    found = detect_patterns(**bars, times=list(range(len(rows))), recent=5)
    assert found == []


def test_too_short_returns_empty():
    bars = _bars([(100.0, 101.0, 99.0, 100.5)])
    assert detect_patterns(**bars, times=[0]) == []
