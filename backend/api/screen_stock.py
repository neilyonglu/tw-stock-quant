"""單股日線技術篩選：uv run python -m backend.api.screen_stock 2330。"""

import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from backend.api.get_stock_data import _fetch_candles
from backend.screening.technical import _blocked, evaluate_technical


def screen_stock(ticker: str) -> dict:
    """透過中台取一年日 K；本入口不直接存取外部行情來源。"""
    try:
        raw = _fetch_candles(ticker, "1y", "1d")
    except (OSError, json.JSONDecodeError) as error:
        return {"ticker": ticker, **_blocked("source_error", str(error))}
    if not isinstance(raw, dict):
        return {"ticker": ticker, **_blocked("invalid_data", "來源不是 JSON 物件")}
    if "error" in raw:
        return {"ticker": ticker, **_blocked("source_error", raw["error"])}
    if raw.get("stale_adjust", False):
        return {"ticker": ticker, **evaluate_technical(pd.DataFrame(), stale_adjust=True)}
    try:
        candles, volume = raw["candles"], raw["volume"]
        if [c["time"] for c in candles] != [v["time"] for v in volume]:
            raise ValueError("K 線與成交量時間不一致")
        df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close"])
        df["volume"] = [v["value"] for v in volume]
        df.index = pd.to_datetime(df.pop("time"), errors="raise")
        today = datetime.now(ZoneInfo("Asia/Taipei")).date()
        if (df.index.date > today).any():
            raise ValueError("來源含未來日期")
        # ponytail: 來源沒有收棒旗標，保守排除當日；日後有可靠旗標再允許當日收盤評分。
        complete = df.loc[df.index.date < today]
        result = evaluate_technical(complete)
        result["excluded_current_day"] = len(df) - len(complete)
        return {"ticker": ticker, **result}
    except (KeyError, TypeError, ValueError) as error:
        return {"ticker": ticker, **_blocked("invalid_data", str(error))}


if __name__ == "__main__":
    result = screen_stock(sys.argv[1] if len(sys.argv) > 1 else "2330")
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
