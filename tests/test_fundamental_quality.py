import copy
import io
import json
from urllib.error import HTTPError, URLError

import pytest

from backend.api import check_fundamentals
from backend.screening.fundamental_quality import assess_fundamentals


def snapshot(ticker="6488", values=None):
    values = values if values is not None else [("2025-12-31", "EPS", 4.62), ("2026-06-30", "EPS", 7.9)]
    return {"ticker": ticker, "source": "FinMind", "dataset": "TaiwanStockFinancialStatements",
            "fetched_at": "2026-10-16T01:00:00+00:00", "start_date": "2025-01-01",
            "end_date": "2026-10-16", "records": [
                {"stock_id": ticker, "date": period, "type": field, "value": value}
                for period, field, value in values]}


def test_known_conflict_blocks_but_preserves_values_and_provenance():
    raw = snapshot()
    original = copy.deepcopy(raw)
    result = assess_fundamentals(raw)
    assert raw == original
    assert result["status"] == "needs_review" and result["can_screen"] is False
    assert result["latest_period"] == "2026-06-30" and result["freshness"] == "unknown"
    assert [c["status"] for c in result["checks"]] == ["needs_review", "matched"]
    conflict = result["checks"][0]
    assert conflict["observed_value"] == 4.62 and conflict["reference_value"] == "4.61"
    assert conflict["unit"] == "TWD/share" and conflict["source_url"].startswith("https://")


def test_recent_fetch_is_not_recent_financial_period():
    raw = snapshot("2330", [("2026-06-30", "Revenue", 1270381000000)])
    result = assess_fundamentals(raw)
    assert result["status"] == "pending_update" and result["can_screen"] is False
    assert result["reviewed_announcement"]["period"] == "2026-09-30"
    assert result["checks"][0]["status"] == "needs_review"
    raw["records"].append({"stock_id": "2330", "date": "2026-09-30", "type": "EPS", "value": 29.43})
    result = assess_fundamentals(raw)
    assert result["freshness"] == "at_least_reviewed_period"
    assert result["status"] == "needs_review"  # 更新期間不會清除其他已知差異。


@pytest.mark.parametrize(("value", "expected"), [(4.61, "matched"), (4.614, "matched"), (4.615, "needs_review")])
def test_precision_follows_reference_display_instead_of_arbitrary_percentage(value, expected):
    result = assess_fundamentals(snapshot(values=[("2025-12-31", "EPS", value), ("2026-06-30", "EPS", 7.9)]))
    assert result["checks"][0]["status"] == expected
    if expected == "matched":
        assert result["can_screen"] is None  # 抽查全過也不代表整份財報已驗證。


def test_short_query_excludes_outside_conflict_and_missing_value_is_not_zero():
    raw = snapshot(values=[("2026-06-30", "EPS", 7.9)])
    raw["start_date"] = "2026-01-01"
    result = assess_fundamentals(raw)
    assert len(result["checks"]) == 1 and result["can_screen"] is None
    raw["records"][0]["value"] = None
    assert assess_fundamentals(raw)["checks"][0]["status"] == "missing_data"
    raw["records"][0]["value"] = 0
    result = assess_fundamentals(raw)
    assert result["checks"][0]["observed_value"] == 0
    assert result["checks"][0]["status"] == "needs_review"


def test_revenue_uses_revenue_month_cash_flow_uses_ytd_and_unreviewed_is_unknown():
    raw = snapshot("2317", [("2026-06-30", "Revenue", 0)])
    assert assess_fundamentals(raw)["can_screen"] is None
    raw["dataset"] = "TaiwanStockCashFlowsStatement"
    assert assess_fundamentals(raw)["period_basis"] == "year_to_date"
    raw["dataset"] = "TaiwanStockMonthRevenue"
    raw["records"] = [{"stock_id": "2317", "date": "2026-10-01", "revenue_year": 2026,
                       "revenue_month": 9, "revenue": 0}]
    result = assess_fundamentals(raw)
    assert result["latest_period"] == "2026-09-01" and result["freshness"] == "unknown"
    raw["records"].append(raw["records"][0].copy())
    assert assess_fundamentals(raw)["status"] == "invalid_data"
    raw["records"] = raw["records"][:1]
    raw["records"][0]["revenue"] = float("nan")
    assert assess_fundamentals(raw)["status"] == "invalid_data"


def test_historical_range_does_not_require_an_announcement_after_query_end():
    raw = snapshot("2330", [("2026-06-30", "Revenue", 1270380250000)])
    raw["end_date"] = "2026-06-30"
    result = assess_fundamentals(raw)
    assert result["freshness"] == "unknown" and result["can_screen"] is None
    assert "reviewed_announcement" not in result


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "7.9"])
def test_invalid_numbers_block_assessment(value):
    assert assess_fundamentals(snapshot(values=[("2026-06-30", "EPS", value)]))["status"] == "invalid_data"


def test_missing_duplicate_and_malformed_data_do_not_pass():
    assert assess_fundamentals(snapshot(values=[]))["status"] == "missing_data"
    raw = snapshot()
    raw["records"].append(raw["records"][0].copy())
    assert assess_fundamentals(raw)["checks"][0]["status"] == "ambiguous_data"
    for invalid in [None, [], {}, {"ticker": "2330"}]:
        assert assess_fundamentals(invalid)["status"] == "invalid_data"


def test_cli_uses_data_service_and_does_not_turn_failures_into_failed_stock(monkeypatch):
    monkeypatch.setenv("DATA_SERVICE_URL", "http://data-service:8001")

    def source(url, timeout):
        assert url == "http://data-service:8001/stocks/6488/fundamentals?dataset=income_statement"
        return io.BytesIO(json.dumps(snapshot()).encode())

    monkeypatch.setattr(check_fundamentals, "urlopen", source)
    assert check_fundamentals.check_fundamentals("6488")["status"] == "needs_review"
    for failure, status in [(URLError("private"), "source_error"),
                            (HTTPError("private", 404, "private", {}, io.BytesIO(
                                json.dumps({"detail": "指定股票與期間沒有這類基本面資料"}).encode())), "missing_data")]:
        def broken(*args, failure=failure, **kwargs):
            raise failure
        monkeypatch.setattr(check_fundamentals, "urlopen", broken)
        result = check_fundamentals.check_fundamentals("6488")
        assert result["status"] == status and result["can_screen"] is False
        assert "private" not in json.dumps(result)


@pytest.mark.parametrize(("body", "status"), [
    (b'{"detail":"Not Found"}', "service_outdated"),
    (b'{"detail":"private"}', "source_error"),
    (b'not json', "source_error"),
    (b'[]', "source_error"),
])
def test_missing_route_is_not_reported_as_missing_financial_data(body, status, monkeypatch):
    def source(*args, **kwargs):
        raise HTTPError("private", 404, "private", {}, io.BytesIO(body))

    monkeypatch.setattr(check_fundamentals, "urlopen", source)
    result = check_fundamentals.check_fundamentals("2330")
    assert result["status"] == status and result["can_screen"] is False
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize(("value", "expected"), [
    (1270380250000, "matched"),
    (1270380251000, "needs_review"),
    (1270381000000, "needs_review"),
])
def test_tsmc_revenue_uses_reviewed_statement_without_clearing_freshness_warning(value, expected):
    raw = snapshot("2330", [("2026-06-30", "Revenue", value)])
    original = copy.deepcopy(raw)
    result = assess_fundamentals(raw)
    assert raw == original
    check = result["checks"][0]
    assert check["status"] == expected
    assert check["reference_value"] == "1270380250000"
    assert check["precision"] == "1000"
    assert check["source_url"].endswith("Consolidated%20Financial%20Statements_E_2.pdf")
    assert result["status"] == "pending_update" and result["can_screen"] is False
    raw["end_date"] = "2026-06-30"
    result = assess_fundamentals(raw)
    assert result["status"] == ("unverified" if expected == "matched" else "needs_review")
    assert result["can_screen"] is (None if expected == "matched" else False)


def test_earnings_release_warning_names_available_period_without_claiming_reviewed_filing():
    raw = snapshot("2330", [("2026-06-30", "Revenue", 1270380250000)])
    original = copy.deepcopy(raw)
    result = assess_fundamentals(raw)
    assert result["reviewed_announcement"]["source_kind"] == "earnings_release"
    assert result["issues"] == ["2026-09-30 業績摘要已公布；FinMind 財報資料目前僅到 2026-06-30。業績摘要不代表完整核閱財報。"]
    assert result["status"] == "pending_update" and result["can_screen"] is False
    assert result["checks"][0]["status"] == "matched"
    assert raw == original
    raw["records"].append({"stock_id": "2330", "date": "2026-09-30", "type": "EPS", "value": 29.43})
    updated = assess_fundamentals(raw)
    assert updated["status"] == "unverified" and updated["can_screen"] is None
    assert updated["issues"] == []


def test_reviewed_filing_warning_stays_distinct_from_earnings_release(monkeypatch):
    from backend.screening import fundamental_quality

    references = copy.deepcopy(fundamental_quality._REFERENCES)
    references["announcements"][0]["source_kind"] = "reviewed_financial_statement"
    monkeypatch.setattr(fundamental_quality, "_REFERENCES", references)
    result = assess_fundamentals(snapshot("2330", [("2026-06-30", "Revenue", 1270380250000)]))
    assert result["status"] == "pending_update" and result["can_screen"] is False
    assert "完整核閱財報已公布" in result["issues"][0]
    assert "業績摘要" not in result["issues"][0]


@pytest.mark.parametrize(("year", "month"), [(2026, 9), (2026, 11), (2099, 9)])
def test_quality_rejects_revenue_period_after_source_date_or_query_end(year, month):
    raw = snapshot("2317")
    raw["dataset"] = "TaiwanStockMonthRevenue"
    raw["records"] = [{"stock_id": "2317", "date": "2026-08-01", "revenue_year": year,
                       "revenue_month": month, "revenue": 100}]
    result = assess_fundamentals(raw)
    assert result["status"] == "invalid_data" and result["can_screen"] is False
    assert result["latest_period"] is None and result["issues"]


def test_quality_accepts_prior_year_revenue_before_query_start():
    raw = snapshot("2317")
    raw.update(dataset="TaiwanStockMonthRevenue", start_date="2026-01-01",
               end_date="2026-01-31")
    raw["records"] = [{"stock_id": "2317", "date": "2026-01-10", "revenue_year": 2025,
                       "revenue_month": 12, "revenue": 100}]
    result = assess_fundamentals(raw)
    assert result["status"] == "unverified" and result["can_screen"] is None
    assert result["latest_period"] == "2025-12-01"


@pytest.mark.parametrize(("dataset", "name"), [
    ("TaiwanStockFinancialStatements", "income_statement"),
    ("TaiwanStockBalanceSheet", "balance_sheet"),
    ("TaiwanStockCashFlowsStatement", "cash_flow"),
])
@pytest.mark.parametrize("duplicate_value", [1, -999])
def test_quality_cli_reports_unreviewed_duplicate_financial_pairs(dataset, name, duplicate_value, monkeypatch):
    raw = snapshot("2317", [("2025-06-30", "UnreviewedField", 1),
                            ("2025-06-30", "OtherField", 2),
                            ("2025-09-30", "UnreviewedField", 3)])
    raw["dataset"] = dataset
    assert assess_fundamentals(raw)["can_screen"] is None
    raw["records"].append({**raw["records"][0], "value": duplicate_value})
    original = copy.deepcopy(raw)
    monkeypatch.setattr(check_fundamentals, "fetch_fundamental_data", lambda *a: raw)
    result = check_fundamentals.check_fundamentals("2317", name)
    assert result["status"] == "needs_review" and result["can_screen"] is False
    assert result["checks"] == []
    assert result["issues"] == ["2025-06-30 UnreviewedField: ambiguous_data"]
    assert raw == original
