"""大盤 + 國際指數，全部來自 yfinance，免金鑰。搬自舊 src/api/get_market_indices.py。"""
import yfinance as yf

from data_service.cache import ttl_cache

GLOBAL_INDICES = [
    ("道瓊工業", "^DJI"),
    ("那斯達克", "^IXIC"),
    ("日經225", "^N225"),
    ("上證指數", "000001.SS"),
]


def _quote(symbol: str) -> dict | None:
    """抓不到就回 None，不要回 0——這個系統的產出會影響投資決策，捏造一個看起來
    合法的 0 比空白危險得多（呼叫端要負責把 None 顯示成「—」之類的缺值樣式）。
    """
    h = yf.Ticker(symbol).history(period="5d").dropna(subset=["Close"])
    if len(h) < 2:
        return None
    last = float(h["Close"].iloc[-1])
    prev = float(h["Close"].iloc[-2])
    return {
        "value": round(last, 2),
        "change": round(last - prev, 2),
        "change_pct": round((last - prev) / prev * 100, 2),
    }


@ttl_cache(seconds=30)
def fetch_market_indices() -> dict:
    # 櫃買指數：yfinance 的 ^TWOII 已查不到資料（2026-07-29 實測 ^TWOII/^TWO/^TPEX
    # 全部回 0 筆），所以 otc 目前一律是 None，前端會顯示「—」。要拿到真的櫃買指數
    # 得另找來源（TPEx OpenAPI），見 todo.md。
    return {
        "taiex": _quote("^TWII"),
        "otc": _quote("^TWOII"),
        "global": [
            {"name": name, **{k: v for k, v in (q or {}).items() if k != "change"}}
            for name, symbol in GLOBAL_INDICES
            if (q := _quote(symbol)) is not None
        ],
    }
