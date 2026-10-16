"""以 twstock 本機代碼表列出上市／上櫃一般股票，不發出網路請求。"""

import json
from collections import Counter

import twstock

MARKET_SUFFIXES = {"上市": ".TW", "上櫃": ".TWO"}


def yahoo_symbol(ticker: str) -> str:
    """裸代碼 → Yahoo 代碼；查不到市場時不猜測後綴。已知 ETF 等仍可直接查詢。"""
    info = twstock.codes.get(ticker)
    if info is None or info.market not in MARKET_SUFFIXES:
        raise ValueError(f"查無上市／上櫃代碼「{ticker}」，請確認代碼或更新 twstock 代碼表")
    return ticker + MARKET_SUFFIXES[info.market]


def stock_universe() -> list[dict[str, str]]:
    """只含一般股票；排除 ETF、權證、特別股與不支援的市場，按代碼排序。"""
    return [
        {"ticker": code, "name": info.name, "market": info.market,
         "symbol": code + MARKET_SUFFIXES[info.market]}
        for code, info in sorted(twstock.codes.items())
        if info.type == "股票" and info.market in MARKET_SUFFIXES
    ]


if __name__ == "__main__":
    stocks = stock_universe()
    print(json.dumps({"total": len(stocks), "markets": dict(Counter(s["market"] for s in stocks))},
                     ensure_ascii=False))
