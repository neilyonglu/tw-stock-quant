import numpy as np
import talib

from src.indicators.trend import ema, macd, sma


def test_sma_matches_talib(ohlcv):
    ours = sma(ohlcv["close"], 20)
    ref = talib.SMA(ohlcv["close"].to_numpy(), 20)
    np.testing.assert_allclose(ours.to_numpy()[19:], ref[19:], rtol=1e-9)


def test_ema_converges_to_talib(ohlcv):
    # TA-Lib 的 EMA 用前 n 根 SMA 當種子，pandas 用第一根；差異隨時間指數衰減，看尾段即可
    ours = ema(ohlcv["close"], 12)
    ref = talib.EMA(ohlcv["close"].to_numpy(), 12)
    np.testing.assert_allclose(ours.to_numpy()[-50:], ref[-50:], rtol=1e-6)


def test_macd_converges_to_talib(ohlcv):
    line, sig, hist = macd(ohlcv["close"])
    ref_line, ref_sig, ref_hist = talib.MACD(ohlcv["close"].to_numpy(), 12, 26, 9)
    np.testing.assert_allclose(line.to_numpy()[-50:], ref_line[-50:], atol=1e-4)
    np.testing.assert_allclose(sig.to_numpy()[-50:], ref_sig[-50:], atol=1e-4)
    np.testing.assert_allclose(hist.to_numpy()[-50:], ref_hist[-50:], atol=1e-4)
