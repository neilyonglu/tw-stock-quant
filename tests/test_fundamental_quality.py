import copy
import io
import json
from urllib.error import HTTPError, URLError

import pytest

from backend.api import check_fundamentals
from backend.screening.fundamental_quality import assess_fundamentals


def snapshot(ticker="6488", values=None):
    values = values if values is not None else [("2025-12-31", "EPS", 4.61), ("2026-06-30", "EPS", 7.9)]
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
    assert conflict["observed_value"] == 4.61 and conflict["reference_value"] == "4.60"
    assert conflict["unit"] == "TWD/share" and conflict["source_url"].startswith("https://")


def test_recent_fetch_is_not_recent_financial_period():
    raw = snapshot("2330", [("2026-06-30", "Revenue", 1270380250000)])
    result = assess_fundamentals(raw)
    assert result["status"] == "pending_update" and result["can_screen"] is False
    assert result["reviewed_announcement"]["period"] == "2026-09-30"
    assert result["checks"][0]["status"] == "needs_review"
    raw["records"].append({"stock_id": "2330", "date": "2026-09-30", "type": "EPS", "value": 29.43})
    result = assess_fundamentals(raw)
    assert result["freshness"] == "at_least_reviewed_period"
    assert result["status"] == "needs_review"  # 更新期間不會清除其他已知差異。


@pytest.mark.parametrize(("value", "expected"), [(4.60, "matched"), (4.604, "matched"), (4.605, "needs_review")])
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
    raw = snapshot("2330", [("2026-06-30", "Revenue", 1270381000000)])
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
                            (HTTPError("private", 404, "private", {}, None), "missing_data")]:
        def broken(*args, failure=failure, **kwargs):
            raise failure
        monkeypatch.setattr(check_fundamentals, "urlopen", broken)
        result = check_fundamentals.check_fundamentals("6488")
        assert result["status"] == status and result["can_screen"] is False
        assert "private" not in json.dumps(result)
