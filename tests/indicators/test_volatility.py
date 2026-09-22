import numpy as np
import pandas as pd
import talib

from src.indicators.volatility import atr


def test_atr_matches_talib_exactly(ohlcv):
    ours = atr(ohlcv["high"], ohlcv["low"], ohlcv["close"], 14)
    ref = talib.ATR(
        ohlcv["high"].to_numpy(), ohlcv["low"].to_numpy(), ohlcv["close"].to_numpy(), 14
    )
    np.testing.assert_allclose(ours.to_numpy()[14:], ref[14:], atol=1e-8)


def test_atr_too_short_is_all_nan():
    s = pd.Series([1.0] * 10)
    assert atr(s + 1, s, s, 14).isna().all()
