#!/usr/bin/env python3
"""
抓大盤指數 + 國際指數，全部來自 yfinance，免金鑰。
對應 frontend MarketIndicesData（lib/types.ts）。
Usage: python3 get_market_indices.py
"""
import json

import yfinance as yf

GLOBAL_INDICES = [
    ("道瓊工業", "^DJI"),
    ("那斯達克", "^IXIC"),
    ("日經225", "^N225"),
    ("上證指數", "000001.SS"),
]


def _quote(symbol: str) -> dict:
    h = yf.Ticker(symbol).history(period="5d")
    if h.empty or len(h) < 2:
        return {"value": 0.0, "change": 0.0, "change_pct": 0.0}
    last = float(h["Close"].iloc[-1])
    prev = float(h["Close"].iloc[-2])
    return {
        "value": round(last, 2),
        "change": round(last - prev, 2),
        "change_pct": round((last - prev) / prev * 100, 2),
    }


def main():
    result = {
        "taiex": _quote("^TWII"),
        "otc": _quote("^TWOII"),
        "global": [
            {"name": name, **{k: v for k, v in _quote(symbol).items() if k != "change"}}
            for name, symbol in GLOBAL_INDICES
        ],
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
