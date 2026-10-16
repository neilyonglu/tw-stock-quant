"""Smoke check: uv run scripts/check_deployment.py [http://127.0.0.1:3000].

The stock request needs access to the external market data source.
"""
import json
import sys
import urllib.request

base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000").rstrip("/")

with urllib.request.urlopen(base, timeout=10) as response:
    assert response.status == 200

for ticker, market in [("2330", "上市"), ("6488", "上櫃")]:
    with urllib.request.urlopen(f"{base}/api/stock/search?q={ticker}", timeout=15) as response:
        assert any(row["ticker"] == ticker for row in json.load(response))

    with urllib.request.urlopen(f"{base}/api/stock/{ticker}?period=6mo", timeout=40) as response:
        stock = json.load(response)
        assert stock["ticker"] == ticker and stock["candles"] and stock["rsi"]
        assert stock["sma20"] and stock["macd"]["line"]
        assert stock["kd"]["k"] and stock["kd"]["d"] and stock["atr14"]
        assert stock["stale_adjust"] is False

    with urllib.request.urlopen(f"{base}/api/stock/{ticker}/profile", timeout=40) as response:
        assert json.load(response)["listed_market"] == market

print("PASS: frontend, TWSE/TPEX sources, Python indicators")
