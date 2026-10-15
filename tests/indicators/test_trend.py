import numpy as np
import pandas as pd
import talib

from backend.indicators.trend import ema, macd, sma


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


def test_macd_matches_documented_ema_recurrence(ohlcv):
    # TradingView 的 EMA/MACD 公式；明確以首價起算，不混用 TA-Lib SMA 種子。
    def reference(values, length):
        previous = float(values[0])
        output = [previous]
        alpha = 2 / (length + 1)
        for value in values[1:]:
            previous = alpha * value + (1 - alpha) * previous
            output.append(previous)
        return np.array(output)

    close = ohlcv["close"].to_numpy()
    expected_line = reference(close, 12) - reference(close, 26)
    expected_signal = reference(expected_line, 9)
    line, signal, histogram = macd(pd.Series(close))
    np.testing.assert_allclose(line, expected_line, atol=1e-10)
    np.testing.assert_allclose(signal, expected_signal, atol=1e-10)
    np.testing.assert_allclose(histogram, expected_line - expected_signal, atol=1e-10)
