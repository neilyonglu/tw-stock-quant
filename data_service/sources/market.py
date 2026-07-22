"""大盤 + 國際指數，全部來自 yfinance，免金鑰。搬自舊 src/api/get_market_indices.py。"""
import yfinance as yf

from data_service.cache import ttl_cache

GLOBAL_INDICES = [
    ("道瓊工業", "^DJI"),
    ("那斯達克", "^IXIC"),
    ("日經225", "^N225"),
    ("上證指數", "000001.SS"),
]


def _quote(symbol: str) -> dict:
    h = yf.Ticker(symbol).history(period="5d").dropna(subset=["Close"])
    if len(h) < 2:
        return {"value": 0.0, "change": 0.0, "change_pct": 0.0}
    last = float(h["Close"].iloc[-1])
    prev = float(h["Close"].iloc[-2])
    return {
        "value": round(last, 2),
        "change": round(last - prev, 2),
        "change_pct": round((last - prev) / prev * 100, 2),
    }


@ttl_cache(seconds=30)
def fetch_market_indices() -> dict:
    return {
        "taiex": _quote("^TWII"),
        "otc": _quote("^TWOII"),
        "global": [
            {"name": name, **{k: v for k, v in _quote(symbol).items() if k != "change"}}
            for name, symbol in GLOBAL_INDICES
        ],
    }
