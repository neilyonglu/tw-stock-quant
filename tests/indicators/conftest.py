import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    """300 根隨機漫步 K 棒，固定 seed 讓結果可重現；夠長讓 EMA 種子差異收斂。"""
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0, 1, 300))
    spread = rng.uniform(0.5, 2.0, 300)
    high = close + spread
    low = close - spread
    open_ = close + rng.normal(0, 0.5, 300)
    open_ = np.clip(open_, low, high)
    volume = rng.integers(1000, 5000, 300).astype(float)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})
