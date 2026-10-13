"""Smoke check: uv run scripts/check_deployment.py [http://127.0.0.1:3000].

The stock request needs access to the external market data source.
"""
import json
import sys
import urllib.request

base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000").rstrip("/")

with urllib.request.urlopen(base, timeout=10) as response:
    assert response.status == 200

with urllib.request.urlopen(f"{base}/api/stock/search?q=2330", timeout=15) as response:
    matches = json.load(response)
    assert any(row["ticker"] == "2330" and row["name"] == "台積電" for row in matches)

with urllib.request.urlopen(f"{base}/api/stock/2330?period=6mo", timeout=40) as response:
    stock = json.load(response)
    assert stock["ticker"] == "2330" and stock["candles"] and stock["rsi"]
    assert stock["sma20"] and stock["macd"]["line"]

print("PASS: frontend, data-service connection, Python indicators")
