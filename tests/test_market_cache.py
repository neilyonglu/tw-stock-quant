import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from backend.data_service import cache, store
from backend.data_service.sources import stock


@pytest.mark.parametrize("close,expected", [
    (10, (11, 9)), (20, (22, 18)), (35, (38.5, 31.5)),
    (42, (46.2, 37.8)), (60, (66, 54)), (100, (110, 90)),
])
def test_limit_prices_round_inward_without_losing_an_exact_tick(close, expected):
    assert stock._limit_prices(close) == expected


def test_failed_adjustment_stays_blocked_until_full_history_is_restored(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cache.db")
    monkeypatch.setattr(stock, "_prev_daily_close", lambda ticker: 100)
    old = [{"time": f"2026-10-{day:02d}", "open": 100, "high": 101,
            "low": 99, "close": 100, "volume": 1000} for day in range(12, 17)]
    adjusted = [{**row, "open": 90, "high": 91, "low": 89, "close": 90} for row in old]
    store.upsert("2330.TW", "1d", old)
    store.record_source_start("2330.TW", "1d", old[0]["time"])
    responses = iter([adjusted, [], [], old, adjusted[-1:], adjusted, adjusted])
    monkeypatch.setattr(stock, "_yf_rows", lambda *args, **kwargs: next(responses))
    assert stock._fetch_candles_persistent("2330", "max", "1d")["stale_adjust"] is True
    # A new callable represents a request after TTL expiry or a service restart.
    fresh_service = cache.ttl_cache(60)(stock._fetch_candles_persistent)
    assert fresh_service("2330", "max", "1d")["stale_adjust"] is True
    partial = stock._fetch_candles_persistent("2330", "max", "1d")
    assert partial["stale_adjust"] is True
    assert partial["candles"][0]["close"] == 100
    recovered = stock._fetch_candles_persistent("2330", "max", "1d")
    assert recovered["stale_adjust"] is False
    assert all(row["close"] == 90 for row in recovered["candles"])


def test_adjustment_invalidates_other_cached_display_periods(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cache.db")
    monkeypatch.setattr(stock, "_prev_daily_close", lambda ticker: 100)
    stock.fetch_candles.cache_clear()
    old = [{"time": f"2026-10-{day:02d}", "open": 100, "high": 101,
            "low": 99, "close": 100, "volume": 1000} for day in range(12, 17)]
    adjusted = [{**row, "open": 90, "high": 91, "low": 89, "close": 90} for row in old]
    store.upsert("2330.TW", "1d", old)
    store.record_source_start("2330.TW", "1d", old[0]["time"])
    responses = iter([old, adjusted, [], [], adjusted, adjusted, adjusted])
    monkeypatch.setattr(stock, "_yf_rows", lambda *args, **kwargs: next(responses))
    assert stock.fetch_candles("2330", "max", "1d")["stale_adjust"] is False
    assert stock.fetch_candles("2330", "6mo", "1d")["stale_adjust"] is True
    assert stock.fetch_candles("2330", "max", "1d")["stale_adjust"] is True
    assert stock.fetch_candles("2330", "1y", "1d")["stale_adjust"] is False
    restored = stock.fetch_candles("2330", "max", "1d")
    assert restored["stale_adjust"] is False
    assert all(row["close"] == 90 for row in restored["candles"])


def test_ttl_expires_and_evicts_without_caching_exceptions(monkeypatch):
    now = [0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: now[0])
    calls = []

    @cache.ttl_cache(10, maxsize=2)
    def fetch(key):
        calls.append(key)
        if key == "error":
            raise ValueError("source unavailable")
        return len(calls)

    assert fetch("a") == fetch("a") == 1
    fetch("b")
    fetch("c")
    assert fetch("a") == 4
    now[0] = 11
    assert fetch("a") == 5
    for _ in range(2):
        with pytest.raises(ValueError):
            fetch("error")
    assert calls.count("error") == 2


def test_expired_cache_values_are_released(monkeypatch):
    import gc
    import weakref

    class Value:
        pass

    now = [0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: now[0])

    @cache.ttl_cache(10)
    def fetch(key):
        return Value()

    first = weakref.ref(fetch("old"))
    now[0] = 11
    fetch("new")
    gc.collect()
    assert first() is None


def test_concurrent_same_key_shares_one_source_request():
    entered, release = threading.Event(), threading.Event()
    calls = []

    @cache.ttl_cache(60)
    def fetch(key):
        calls.append(key)
        entered.set()
        assert release.wait(5)
        return key

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch, "same") for _ in range(4)]
        assert entered.wait(5)
        release.set()
        assert [future.result(timeout=5) for future in futures] == ["same"] * 4
    assert calls == ["same"]
