import io
import json
from datetime import date
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest
from fastapi import HTTPException

from backend.data_service import main
from backend.data_service.sources import fundamental
from backend.data_service.sources import stock as stock_source


@pytest.mark.parametrize("dataset", fundamental.DATASETS)
def test_raw_data_dates_values_token_and_cache(dataset, monkeypatch):
    records = [{"date": "2025-06-30", "stock_id": "6488", "type": "EPS", "value": 0},
               {"date": "2025-03-31", "stock_id": "6488", "type": "EPS", "value": -1},
               {"date": "2025-03-31", "stock_id": "6488", "type": "Other", "value": None}]
    if dataset == "monthly_revenue":
        records = [{"date": "2025-06-01", "stock_id": "6488", "revenue_year": 2025,
                    "revenue_month": 5, "revenue": 0, "create_time": ""}]
    elif dataset == "dividends":
        records = [{"date": "2025-06-01", "stock_id": "6488",
                    "CashEarningsDistribution": 0, "AnnouncementDate": "2025-05-01"}]
    calls = []

    def source(request, timeout):
        calls.append(request)
        assert request.get_header("Authorization") == "Bearer private-token"
        assert "private-token" not in request.full_url
        assert "data_id=6488" in request.full_url
        assert fundamental.DATASETS[dataset] in request.full_url
        assert timeout == 30
        return io.BytesIO(json.dumps({"status": 200, "data": records}).encode())

    monkeypatch.setenv("FINMIND_TOKEN", "private-token")
    monkeypatch.setattr(fundamental, "urlopen", source)
    # 獨立 cache，避免測試順序互相影響；使用正式 decorator。
    monkeypatch.setattr(fundamental, "fetch_fundamentals",
                        fundamental.ttl_cache(1800)(fundamental.fetch_fundamentals.__wrapped__))
    result = main.get_fundamentals("6488", dataset, date(2025, 1, 1), date(2025, 12, 31))
    assert result["source"] == "FinMind" and result["ticker"] == "6488"
    assert result["records"] == sorted(records, key=lambda row: row["date"])
    assert "private-token" not in json.dumps(result)
    assert main.get_fundamentals("6488", dataset, date(2025, 1, 1), date(2025, 12, 31)) == result
    assert len(calls) == 1


@pytest.mark.parametrize(("payload", "status"), [
    ({"status": 429, "msg": "secret"}, 503),
    ({"status": 401, "msg": "secret"}, 502),
    ({"status": 200, "data": []}, 404),
    ({"status": 200, "data": None}, 502),
    ({"status": 200, "data": [{"stock_id": "2330", "date": "2025-03-31"}]}, 502),
    ({"status": 200, "data": [{"stock_id": "6488", "date": "2025-03-31",
                               "type": "EPS", "value": float("nan")}]}, 502),
    ([], 502),
])
def test_invalid_source_is_not_empty_success_or_cached(payload, status, monkeypatch):
    replies = iter([payload, {"status": 200, "data": [
        {"stock_id": "6488", "date": "2025-03-31", "type": "EPS", "value": 0}]}])
    monkeypatch.setattr(fundamental, "urlopen", lambda *a, **kw:
                        io.BytesIO(json.dumps(next(replies)).encode()))
    fetch = fundamental.ttl_cache(1800)(fundamental.fetch_fundamentals.__wrapped__)
    with pytest.raises(HTTPException) as error:
        fetch("6488", "income_statement", date(2025, 1, 1), date(2025, 12, 31))
    assert error.value.status_code == status and "secret" not in error.value.detail
    assert fetch("6488", "income_statement", date(2025, 1, 1), date(2025, 12, 31))["records"]


@pytest.mark.parametrize(("failure", "status"), [
    (HTTPError("https://example.invalid", 429, "secret", {}, None), 503),
    (HTTPError("https://example.invalid", 403, "secret", {}, None), 502),
    (TimeoutError("secret"), 504),
    (URLError("secret"), 502),
    (ValueError("secret"), 502),
])
def test_transport_errors_are_safe(failure, status, monkeypatch):
    def source(*args, **kwargs):
        raise failure

    monkeypatch.setattr(fundamental, "urlopen", source)
    with pytest.raises(HTTPException) as error:
        fundamental.fetch_fundamentals.__wrapped__(
            "2330", "income_statement", date(2025, 1, 1), date(2025, 12, 31))
    assert error.value.status_code == status and "secret" not in error.value.detail


def test_invalid_request_does_not_call_source(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("invalid request reached source")

    monkeypatch.setattr(fundamental, "fetch_fundamentals", unexpected)
    for ticker, start, end, status in [
        ("not-a-stock", date(2025, 1, 1), date(2025, 2, 1), 404),
        ("2330", date(2025, 2, 1), date(2025, 1, 1), 422),
        ("2330", date(2025, 1, 1), date(2099, 1, 1), 422),
    ]:
        with pytest.raises(HTTPException) as error:
            main.get_fundamentals(ticker, "income_statement", start, end)
        assert error.value.status_code == status


@pytest.mark.parametrize(("value", "expected"), [(0, 0), (-1.25, -1.25), (None, None), (float("nan"), None), (True, None)])
def test_profile_preserves_real_zero_and_negative_eps_but_rejects_invalid_numbers(value, expected, monkeypatch):
    info = {"trailingEps": value, "dividendYield": 0, "marketCap": float("nan"),
            "numberOfAnalystOpinions": float("inf"), "fiftyTwoWeekLow": 0}
    monkeypatch.setattr(stock_source.yf, "Ticker", lambda symbol: SimpleNamespace(info=info))
    result = stock_source.fetch_profile.__wrapped__("2330")
    assert result["eps"] == expected and result["dividend_yield"] == 0
    assert result["market_cap"] is None and result["analyst_count"] is None
    assert result["week52_low"] is None  # 價格欄位的 0 仍不可冒充有效報價。
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(("year", "month"), [(2025, 7), (2099, 5)])
def test_revenue_period_cannot_follow_source_date_or_query_end(year, month, monkeypatch):
    records = [{"stock_id": "6488", "date": "2025-06-10", "revenue_year": year,
                "revenue_month": month, "revenue": 100}]
    monkeypatch.setattr(fundamental, "urlopen", lambda *a, **kw:
                        io.BytesIO(json.dumps({"status": 200, "data": records}).encode()))
    with pytest.raises(HTTPException) as error:
        fundamental.fetch_fundamentals.__wrapped__(
            "6488", "monthly_revenue", date(2025, 6, 1), date(2025, 12, 31))
    assert error.value.status_code == 502


def test_revenue_month_before_query_start_is_valid_when_source_date_is_in_range(monkeypatch):
    records = [{"stock_id": "6488", "date": "2025-01-10", "revenue_year": 2024,
                "revenue_month": 12, "revenue": 100}]
    monkeypatch.setattr(fundamental, "urlopen", lambda *a, **kw:
                        io.BytesIO(json.dumps({"status": 200, "data": records}).encode()))
    raw = fundamental.fetch_fundamentals.__wrapped__(
        "6488", "monthly_revenue", date(2025, 1, 1), date(2025, 1, 31))
    assert raw["records"] == records
