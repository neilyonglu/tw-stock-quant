import json
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from backend.api.screen_stock import screen_stock
from backend.screening import technical


@pytest.fixture
def candles():
    close = 100 + np.arange(80) * 0.2 + np.sin(np.arange(80)) * 2
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": [1000] * 79 + [1600],
        },
        index=pd.date_range("2020-01-01", periods=80),
    )


def controlled_indicators(df):
    """只控制指標以隔離規則邊界；真實計算另有端到端檢查。"""
    result = df.copy()
    for key, value in {
        "sma20": 110,
        "sma60": 100,
        "rsi14": 55,
        "macd": 2,
        "macd_signal": 1,
        "k": 60,
        "d": 50,
    }.items():
        result[key] = float(value)
    return result


def test_real_calculations_and_json_are_reproducible(candles):
    before = candles.copy(deep=True)
    result = technical.evaluate_technical(candles)
    assert result["status"] == "evaluated"
    assert result["score"] == sum(rule["points"] for rule in result["rules"])
    assert result["passed"] == all(rule["passed"] for rule in result["rules"][:4])
    assert result == json.loads(json.dumps(result, allow_nan=False))
    pd.testing.assert_frame_equal(candles, before)


def test_all_gates_and_optional_pattern(candles, monkeypatch):
    monkeypatch.setattr(technical, "add_indicators", controlled_indicators)
    monkeypatch.setattr(technical, "detect_patterns", lambda *args: [])
    result = technical.evaluate_technical(candles)
    assert result["passed"] is True and result["score"] == 95
    # 舊型態不得加分；當根型態才加 5 分，兩者都不是必要門檻。
    for when, expected in [(candles.index[-2], 95), (candles.index[-1], 100)]:
        monkeypatch.setattr(
            technical,
            "detect_patterns",
            lambda *args, when=when: [
                {"time": when.isoformat(), "name": "錘子線", "signal": "bullish"}
            ],
        )
        assert technical.evaluate_technical(candles)["score"] == expected


@pytest.mark.parametrize(
    ("rsi", "last_volume", "passed", "score"),
    [
        (40, 1600, True, 95),
        (70, 1600, True, 95),
        (39.99, 1600, False, 70),
        (70.01, 1600, False, 70),
        (55, 1500, False, 80),
    ],
)
def test_rsi_and_volume_boundaries(candles, monkeypatch, rsi, last_volume, passed, score):
    def indicators(df):
        result = controlled_indicators(df)
        result["rsi14"] = rsi
        return result

    candles.iloc[-1, candles.columns.get_loc("volume")] = last_volume
    monkeypatch.setattr(technical, "add_indicators", indicators)
    monkeypatch.setattr(technical, "detect_patterns", lambda *args: [])
    result = technical.evaluate_technical(candles)
    assert result["passed"] is passed and result["score"] == score


@pytest.mark.parametrize(
    ("cross", "k", "expected"), [(False, 60, False), (True, 60, True), (True, 80, False)]
)
def test_real_crossing_not_line_position(candles, monkeypatch, cross, k, expected):
    def indicators(df):
        result = controlled_indicators(df)
        result["rsi14"] = 80
        result["macd"] = -1
        result["macd_signal"] = -2
        result["k"] = k
        result["d"] = k - 5
        if cross:
            result.iloc[-2, result.columns.get_loc("macd")] = -3
            result.iloc[-2, result.columns.get_loc("k")] = k - 10
        return result

    monkeypatch.setattr(technical, "add_indicators", indicators)
    monkeypatch.setattr(technical, "detect_patterns", lambda *args: [])
    result = technical.evaluate_technical(candles)
    rules = {rule["id"]: rule for rule in result["rules"]}
    assert rules["macd"]["values"]["golden_cross"] is cross
    assert rules["momentum"]["passed"] is expected


def test_required_gate_cannot_be_replaced_by_bonus(candles, monkeypatch):
    def indicators(df):
        result = controlled_indicators(df)
        result["sma20"] = result["close"]  # 等於不算站上。
        return result

    monkeypatch.setattr(technical, "add_indicators", indicators)
    monkeypatch.setattr(
        technical,
        "detect_patterns",
        lambda *args: [
            {"time": candles.index[-1].isoformat(), "name": "錘子線", "signal": "bullish"}
        ],
    )
    result = technical.evaluate_technical(candles)
    assert result["passed"] is False and result["score"] == 70


@pytest.mark.parametrize(
    "fault",
    [
        "short",
        "nan",
        "infinite",
        "zero_price",
        "bad_high",
        "negative_volume",
        "duplicate",
        "reversed",
        "intraday",
        "zero_baseline",
    ],
)
def test_missing_or_invalid_data_is_not_a_failed_trade(candles, fault):
    if fault == "short":
        candles = candles.iloc[:59]
    elif fault == "nan":
        candles.iloc[-1, 0] = np.nan
    elif fault == "infinite":
        candles.iloc[-1, 0] = np.inf
    elif fault == "zero_price":
        candles.iloc[-1, 0] = 0
    elif fault == "bad_high":
        candles.iloc[-1, 1] = 1
    elif fault == "negative_volume":
        candles.iloc[-1, 4] = -1
    elif fault == "duplicate":
        candles.index = [candles.index[0]] * len(candles)
    elif fault == "reversed":
        candles = candles.iloc[::-1]
    elif fault == "intraday":
        candles.index += pd.Timedelta(minutes=5)
    elif fault == "zero_baseline":
        candles.iloc[-6:-1, 4] = 0
    result = technical.evaluate_technical(candles)
    assert result["status"] in {"invalid_data", "insufficient_data"}
    assert result["score"] is None and result["passed"] is None


def test_stale_adjustment_does_not_compute(candles):
    with patch.object(technical, "add_indicators") as calculate:
        result = technical.evaluate_technical(candles, stale_adjust=True)
    assert result["status"] == "stale_adjustment"
    assert result["score"] is None
    calculate.assert_not_called()


def test_cli_adapter_uses_daily_service_and_excludes_current_day(candles):
    today = pd.Timestamp(datetime.now(ZoneInfo("Asia/Taipei")).date())
    current = candles.tail(1).copy()
    current.index = pd.DatetimeIndex([today])
    candles = pd.concat([candles, current])
    raw = {
        "candles": [
            {"time": time.date().isoformat(), **row.drop("volume").to_dict()}
            for time, row in candles.iterrows()
        ],
        "volume": [
            {"time": time.date().isoformat(), "value": row["volume"]}
            for time, row in candles.iterrows()
        ],
    }
    with patch("backend.api.screen_stock._fetch_candles", return_value=raw) as fetch:
        result = screen_stock("6488")
    fetch.assert_called_once_with("6488", "1y", "1d")
    assert result["ticker"] == "6488" and result["status"] == "evaluated"
    assert result["excluded_current_day"] == 1 and result["bars"] == 80
    raw["volume"][-1]["time"] = "2020-01-01"
    with patch("backend.api.screen_stock._fetch_candles", return_value=raw):
        assert screen_stock("6488")["status"] == "invalid_data"


def test_adapter_source_failures_do_not_become_scores():
    with patch("backend.api.screen_stock._fetch_candles", side_effect=OSError("offline")):
        result = screen_stock("6488")
    assert result["status"] == "source_error" and result["score"] is None
    with patch("backend.api.screen_stock._fetch_candles", return_value={"stale_adjust": True}):
        assert screen_stock("6488")["status"] == "stale_adjustment"
    with patch("backend.api.screen_stock._fetch_candles", return_value={"error": "not found"}):
        assert screen_stock("6488")["status"] == "source_error"
