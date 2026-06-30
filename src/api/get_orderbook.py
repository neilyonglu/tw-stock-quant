#!/usr/bin/env python3
"""
五檔報價：twstock.realtime 直接拿 TWSE/TPEx 的即時委買委賣，免金鑰、真資料。
盤前/盤後可能沒有掛單，回傳的某幾檔會是 "-"，這裡濾掉。
對應 frontend OrderBookData（lib/types.ts）。
Usage: python3 get_orderbook.py <ticker>
"""
import json
import sys

import twstock


def _levels(prices: list, volumes: list) -> list:
    out = []
    for p, v in zip(prices, volumes):
        if p == "-" or v == "-":
            continue
        out.append({"price": round(float(p), 2), "volume": int(v)})
    return out


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "2330"

    quote = twstock.realtime.get(ticker)
    if not quote.get("success"):
        print(json.dumps({"error": f"No realtime quote for {ticker}"}))
        sys.exit(1)

    rt = quote["realtime"]
    result = {
        "asks": _levels(rt["best_ask_price"], rt["best_ask_volume"]),
        "bids": _levels(rt["best_bid_price"], rt["best_bid_volume"]),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
