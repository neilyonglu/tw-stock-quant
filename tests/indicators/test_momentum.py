import numpy as np
import pandas as pd
import talib

from src.indicators.momentum import kd, rsi


def test_rsi_matches_talib_exactly(ohlcv):
    # TA-Lib 的 RSI 就是 Wilder 原版（SMA 種子 + 遞迴平滑），應該逐根吻合
    ours = rsi(ohlcv["close"], 14)
    ref = talib.RSI(ohlcv["close"].to_numpy(), 14)
    np.testing.assert_allclose(ours.to_numpy()[14:], ref[14:], atol=1e-8)


def test_rsi_too_short_is_all_nan():
    assert rsi(pd.Series([1.0, 2.0, 3.0]), 14).isna().all()


def test_rsi_all_up_is_100():
    out = rsi(pd.Series(np.arange(1.0, 31.0)), 14)
    assert out.iloc[-1] == 100.0


def test_kd_hand_computed():
    # 9 根全部同一區間 high=110 low=90，close 第 9 根=100 → RSV=50，K/D 從 50 起算保持 50；
    # 第 10 根 close=110（區間頂）→ RSV=100 → K = 50*2/3 + 100/3 = 66.67，D = 50*2/3 + 66.67/3 = 55.56
    high = pd.Series([110.0] * 10)
    low = pd.Series([90.0] * 10)
    close = pd.Series([100.0] * 9 + [110.0])
    k, d = kd(high, low, close, window=9)
    assert k.iloc[:8].isna().all()
    assert k.iloc[8] == 50.0 and d.iloc[8] == 50.0
    assert abs(k.iloc[9] - 66.6667) < 1e-3
    assert abs(d.iloc[9] - 55.5556) < 1e-3


def test_kd_stays_in_range(ohlcv):
    k, d = kd(ohlcv["high"], ohlcv["low"], ohlcv["close"])
    assert k.dropna().between(0, 100).all()
    assert d.dropna().between(0, 100).all()


def test_kd_flat_market_is_neutral():
    # 連續一價鎖死（漲停/跌停）區間高＝低，RSV 無定義，慣例當 50
    flat = pd.Series([100.0] * 12)
    k, d = kd(flat, flat, flat)
    assert (k.dropna() == 50.0).all()
