#!/usr/bin/env python3
"""
個股基本資料：產業別/上市櫃別來自 twstock（本地查表），本益比/股價淨值比/
殖利率/市值/股本來自 yfinance .info。月營收目前沒有資料來源（Phase 4 才接
CasualMarket），先用 mock 占位。
對應 frontend StockProfile（lib/types.ts）。
Usage: python3 get_stock_profile.py <ticker>
"""
import json
import sys

import twstock
import yfinance as yf

# mock：近 6 個月營收，等 Phase 4 CasualMarket /financial/revenue 接上後替換成真資料
_MOCK_MONTHLY_REVENUE = [
    {"month": "2026-01", "revenue": 2150.3, "yoy": 8.4},
    {"month": "2026-02", "revenue": 1980.1, "yoy": 6.1},
    {"month": "2026-03", "revenue": 2310.5, "yoy": 11.2},
    {"month": "2026-04", "revenue": 2402.8, "yoy": 13.7},
    {"month": "2026-05", "revenue": 2455.0, "yoy": 14.9},
    {"month": "2026-06", "revenue": 2510.2, "yoy": 15.8},
]


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"

    code_info = twstock.codes.get(ticker)
    industry = code_info.group if code_info else "未知"
    listed_market = "上市" if code_info and code_info.market == "上市" else "上櫃"

    info = yf.Ticker(f"{ticker}.TW").info

    market_cap = info.get("marketCap")
    shares = info.get("sharesOutstanding")

    result = {
        "industry": industry,
        "listed_market": listed_market,
        "market_cap": round(market_cap / 1e8, 1) if market_cap else 0,
        "shares_outstanding": round(shares / 1e8, 2) if shares else 0,
        "pe_ratio": round(info["trailingPE"], 2) if info.get("trailingPE") else None,
        "pb_ratio": round(info["priceToBook"], 2) if info.get("priceToBook") else None,
        "dividend_yield": round(info["dividendYield"], 2) if info.get("dividendYield") else None,
        "monthly_revenue": _MOCK_MONTHLY_REVENUE,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
