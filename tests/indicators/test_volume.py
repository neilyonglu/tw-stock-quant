import pandas as pd

from src.indicators.volume import volume_ratio


def test_volume_ratio_excludes_latest_bar():
    # 前 5 根平均 100，最新 150 → 1.5
    assert volume_ratio(pd.Series([100.0] * 5 + [150.0])) == 1.5


def test_volume_ratio_short_series_uses_full_mean():
    assert volume_ratio(pd.Series([100.0, 200.0])) == 200.0 / 150.0


def test_volume_ratio_zero_volume_is_neutral():
    assert volume_ratio(pd.Series([0.0] * 6)) == 1.0
