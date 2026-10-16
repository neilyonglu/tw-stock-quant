"""日 K 單股技術面條件。分數是規則符合度，不是勝率或買進建議。"""

import math

import pandas as pd

from backend.indicators import add_indicators, detect_patterns, volume_ratio


def _blocked(status: str, reason: str) -> dict:
    return {
        "rule_version": "technical-v1",
        "scope": "technical_only",
        "status": status,
        "passed": None,
        "score": None,
        "score_max": 100,
        "rules": [],
        "reason": reason,
    }


def evaluate_technical(df: pd.DataFrame, *, stale_adjust: bool = False) -> dict:
    """輸入已收完、升冪且不重複的日 K（DatetimeIndex、OHLCV），不修改原資料。

    60 根供 SMA60；交叉比較相鄰兩根，沒有交叉就不冒稱事件。
    預設權重及門檻是研究版本，尚未經回測最佳化。
    """
    if stale_adjust:
        return _blocked("stale_adjustment", "價格還原更新失敗，暫停技術面評分")
    columns = ["open", "high", "low", "close", "volume"]
    if not df.columns.is_unique or not set(columns).issubset(df.columns):
        return _blocked("invalid_data", "缺少 OHLCV 欄位")
    if (
        not isinstance(df.index, pd.DatetimeIndex)
        or df.index.hasnans
        or not df.index.is_monotonic_increasing
        or not df.index.is_unique
        or not df.index.equals(df.index.normalize())
    ):
        return _blocked("invalid_data", "日 K 必須使用有效、升冪且不重複的日期索引")
    values = df[columns].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any() or not values.map(math.isfinite).all().all():
        return _blocked("invalid_data", "OHLCV 有缺值或非有限數值")
    prices = values[["open", "high", "low", "close"]]
    if (
        (prices <= 0).any().any()
        or (values["volume"] < 0).any()
        or (values["high"] < prices.max(axis=1)).any()
        or (values["low"] > prices.min(axis=1)).any()
    ):
        return _blocked("invalid_data", "價格必須大於零、成交量不可負數，且高低價須包住開收盤")
    if len(values) < 60:
        return _blocked("insufficient_data", f"需至少 60 根完整日 K，目前只有 {len(values)} 根")
    baseline = values["volume"].iloc[-6:-1].mean()
    if not math.isfinite(baseline):
        return _blocked("invalid_data", "前 5 根平均成交量超出可計算範圍")
    if baseline <= 0:
        return _blocked("insufficient_data", "前 5 根平均成交量為零，量能無法比較")
    ind = add_indicators(values)
    now, before = ind.iloc[-1], ind.iloc[-2]
    required = [now[key] for key in ["sma20", "sma60", "rsi14", "macd", "macd_signal", "k", "d"]]
    required += [before[key] for key in ["macd", "macd_signal", "k", "d"]]
    if not all(math.isfinite(value) for value in required):
        return _blocked("insufficient_data", "必要指標沒有有效值，暫停判讀")

    macd_cross = before["macd"] <= before["macd_signal"] and now["macd"] > now["macd_signal"]
    kd_cross = before["k"] <= before["d"] and now["k"] > now["d"]
    rsi_ok = 40 <= now["rsi14"] <= 70
    kd_ok = kd_cross and now["k"] < 80
    ratio = volume_ratio(values["volume"])
    if not math.isfinite(ratio):
        return _blocked("invalid_data", "量比超出可計算範圍")
    times = [time.isoformat() for time in values.index]
    patterns = detect_patterns(
        values["open"], values["high"], values["low"], values["close"], times
    )
    bullish = [p["name"] for p in patterns if p["time"] == times[-1] and p["signal"] == "bullish"]
    rules = []

    def rule(key: str, passed: bool, weight: int, reason: str, readings: dict):
        passed = bool(passed)
        rules.append(
            {
                "id": key,
                "passed": passed,
                "points": weight if passed else 0,
                "max_points": weight,
                "reason": reason,
                "values": readings,
            }
        )

    rule(
        "trend",
        now["close"] > now["sma20"] > now["sma60"],
        30,
        f"需收盤 > SMA20 > SMA60；目前 {now['close']:.2f} / {now['sma20']:.2f} / {now['sma60']:.2f}",
        {"close": float(now["close"]), "sma20": float(now["sma20"]), "sma60": float(now["sma60"])},
    )
    rule(
        "macd",
        now["macd"] > 0 or macd_cross,
        25,
        f"需 MACD > 0 或本根剛金叉；MACD {now['macd']:.4f}，本根金叉：{'是' if macd_cross else '否'}",
        {
            "line": float(now["macd"]),
            "signal": float(now["macd_signal"]),
            "golden_cross": bool(macd_cross),
        },
    )
    rule(
        "momentum",
        rsi_ok or kd_ok,
        25,
        f"需 RSI 40–70（含邊界），或 KD 本根金叉且 K < 80；RSI {now['rsi14']:.2f}，K {now['k']:.2f}，KD 金叉：{'是' if kd_cross else '否'}",
        {
            "rsi14": float(now["rsi14"]),
            "k": float(now["k"]),
            "d": float(now["d"]),
            "kd_golden_cross": bool(kd_cross),
        },
    )
    rule(
        "volume",
        ratio > 1.5,
        15,
        f"需本根量 / 前 5 根均量 > 1.5；目前 {ratio:.4f} 倍（均量不含本根）",
        {"ratio": ratio, "baseline": float(baseline)},
    )
    rule(
        "pattern",
        bool(bullish),
        5,
        "當根偏多型態加分：" + ("、".join(bullish) if bullish else "無"),
        {"bullish": bullish},
    )
    return {
        "rule_version": "technical-v1",
        "scope": "technical_only",
        "status": "evaluated",
        "as_of": times[-1],
        "bars": len(values),
        "passed": all(r["passed"] for r in rules[:4]),
        "score": sum(r["points"] for r in rules),
        "score_max": 100,
        "rules": rules,
    }
