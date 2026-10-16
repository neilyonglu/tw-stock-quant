import io
import json
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest
import twstock
from fastapi import HTTPException

from backend.api import get_stock_data
from backend.data.universe import stock_universe, yahoo_symbol
from backend.data_service import main, store
from backend.data_service.sources import stock


def test_universe_filters_sorts_and_matches_search(monkeypatch):
    records = {
        "6488": ("股票", "上櫃", "環球晶"),
        "2330": ("股票", "上市", "台積電"),
        "0050": ("ETF", "上市", "元大台灣50"),
        "00679B": ("ETF", "上櫃", "元大美債20年"),
        "000001": ("權證", "上市", "測試權證"),
        "1234A": ("特別股", "上市", "測試特別股"),
        "9999": ("股票", "興櫃", "測試興櫃"),
    }
    monkeypatch.setattr(twstock, "codes", {
        code: SimpleNamespace(type=kind, market=market, name=name)
        for code, (kind, market, name) in records.items()
    })
    assert stock_universe() == [
        {"ticker": "2330", "name": "台積電", "market": "上市", "symbol": "2330.TW"},
        {"ticker": "6488", "name": "環球晶", "market": "上櫃", "symbol": "6488.TWO"},
    ]
    assert stock._stock_index.__wrapped__() == [("2330", "台積電"), ("6488", "環球晶")]
    monkeypatch.setattr(stock, "_stock_index", stock._stock_index.__wrapped__)
    assert stock.search_stocks("環球晶") == [{"ticker": "6488", "name": "環球晶"}]
    assert stock.search_stocks("0050") == []
    assert yahoo_symbol("0050") == "0050.TW"  # 排除選股清單不等於禁止原有 ETF 直查。
    assert yahoo_symbol("00679B") == "00679B.TWO"
    with pytest.raises(ValueError):
        yahoo_symbol("9999")


@pytest.mark.parametrize(("ticker", "symbol", "market"), [
    ("2330", "2330.TW", "上市"), ("6488", "6488.TWO", "上櫃"),
])
def test_market_routing_cache_and_indicators(ticker, symbol, market, tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cache.db")
    # 既有正確上市快取保持不動；同名錯誤後綴的庫存不可污染上櫃資料。
    if market == "上櫃":
        store.upsert(ticker + ".TW", "1d", [{"time": "2020-01-01", "open": 1,
                     "high": 1, "low": 1, "close": 1, "volume": 1}])
    index = pd.bdate_range(end=pd.Timestamp.now(tz="Asia/Taipei").normalize(), periods=80)
    frame = pd.DataFrame({"Open": range(100, 180), "High": range(102, 182),
                          "Low": range(99, 179), "Close": range(101, 181),
                          "Volume": [1000] * 80}, index=index)
    client = SimpleNamespace(history=lambda **kwargs: frame.tail(5) if "start" in kwargs else frame,
                             info={"marketCap": 100_000_000})
    calls = []

    def source(name):
        calls.append(name)
        return client

    monkeypatch.setattr(stock.yf, "Ticker", source)
    monkeypatch.setattr(stock, "fetch_candles", stock.fetch_candles.__wrapped__)
    # 避免既有 TTL 讓本測試略過前收盤的來源驗證。
    monkeypatch.setattr(stock, "_prev_daily_close", stock._prev_daily_close.__wrapped__)
    raw = main.get_candles(ticker)
    assert len(raw["candles"]) == 80 and raw["stale_adjust"] is False
    assert store.coverage(symbol, "1d") is not None
    again = main.get_candles(ticker)
    assert again == raw  # SQLite 增量重疊與首抓一致。
    assert main.get_candles(ticker, "1d", "5m")["candles"]  # 非持久化路徑。
    if market == "上櫃":
        assert store.rows_since(ticker + ".TW", "1d", None)[0]["close"] == 1
    profile = stock.fetch_profile.__wrapped__(ticker)
    assert profile["listed_market"] == market
    assert profile["market_cap"] == 1
    # 分時也必須通過同一市場解析；其餘分時格式化仍由原函式處理。
    with patch.object(main.intraday, "fetch_intraday", return_value={"points": []}) as intraday:
        main.get_stock_intraday(ticker)
        intraday.assert_called_once_with(symbol)
    assert calls and set(calls) == {symbol}
    output = io.StringIO()
    with patch.object(get_stock_data, "_fetch_candles", return_value=raw), \
         patch("sys.argv", ["get_stock_data", ticker]), redirect_stdout(output):
        get_stock_data.main()
    result = json.loads(output.getvalue())
    assert result["ticker"] == ticker
    assert result["candles"] == raw["candles"]
    assert result["rsi"] and result["kd"]["k"] and result["atr14"]


@pytest.mark.parametrize("endpoint", [main.get_candles, main.get_profile,
                                     main.get_stock_intraday, main.get_orderbook])
def test_unknown_stock_is_404_without_network(endpoint):
    with patch.object(stock.yf, "Ticker") as source, \
         patch.object(stock.twstock.realtime, "get") as realtime:
        with pytest.raises(HTTPException) as error:
            endpoint("not-a-stock")
        assert error.value.status_code == 404
        source.assert_not_called()
        realtime.assert_not_called()


def test_installed_universe_has_both_markets():
    universe = stock_universe()
    assert {s["market"] for s in universe} == {"上市", "上櫃"}
    assert len({s["ticker"] for s in universe}) == len(universe)
    assert yahoo_symbol("2330") == "2330.TW"
    assert yahoo_symbol("6488") == "6488.TWO"
