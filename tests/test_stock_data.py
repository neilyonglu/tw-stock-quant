"""Offline check of main's existing stock JSON contract."""
import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "stock_data", Path(__file__).resolve().parents[1] / "backend/api/get_stock_data.py"
)
stock_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stock_data)


class StockDataTest(unittest.TestCase):
    def test_backend_package_and_existing_database_location(self):
        from backend.data_service import store
        from backend.data_service.main import health, search_stocks

        self.assertEqual(store.DB_PATH, Path(__file__).resolve().parents[1] / "data/cache.db")
        self.assertEqual(health(), {"status": "ok"})
        self.assertEqual(search_stocks("2330")[0]["ticker"], "2330")

    def test_existing_contract_without_market_network(self):
        candles = [
            {"time": (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
             "open": 100 + i, "high": 102 + i, "low": 99 + i, "close": 101 + i}
            for i in range(80)
        ]
        raw = {"candles": candles,
               "volume": [{"time": c["time"], "value": 1000, "color": "#EF5350"} for c in candles],
               "limit_up": 198, "limit_down": 162}
        output = io.StringIO()
        with patch.object(stock_data, "_fetch_candles", return_value=raw), \
             patch("sys.argv", ["get_stock_data.py", "2330"]), redirect_stdout(output):
            stock_data.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result["ticker"], "2330")
        self.assertEqual(result["candles"], candles)
        self.assertEqual(len(result["sma20"]), 61)
        self.assertEqual(len(result["rsi"]), 66)
        self.assertEqual(result["latest"]["price"], 180)
        self.assertEqual(result["patterns"], [])


if __name__ == "__main__":
    unittest.main()
