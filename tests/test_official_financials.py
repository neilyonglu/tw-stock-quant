"""Official amounts retain source identity, unknowns and evidence across batch runs."""

import io
import json
from contextlib import closing
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException

from backend.api import audit_financials as batch
from backend.data_service import main, store
from backend.data_service.sources import official


def filing(ticker="2409", extra="", unit="iso4217:TWD", amount="76,256,091"):
    return f'''<html>合併財務報告
    <ix:nonNumeric name="tifrs-notes:CompanyID">{ticker}</ix:nonNumeric>
    <ix:nonNumeric name="tifrs-notes:Year">2025</ix:nonNumeric>
    <ix:nonNumeric name="tifrs-notes:ReportCategory">Consolidated report</ix:nonNumeric>
    <xbrli:context id="now"><xbrli:entity><xbrli:identifier>{ticker}</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:instant>2025-12-31</xbrli:instant></xbrli:period></xbrli:context>
    <xbrli:unit id="money"><xbrli:measure>{unit}</xbrli:measure></xbrli:unit>
    <ix:nonFraction name="ifrs-full:LongtermBorrowings" contextRef="now" unitRef="money"
        format="ixt:numdotdecimal" scale="3">{amount}</ix:nonFraction>{extra}</html>'''


def test_parser_preserves_units_scope_unknowns_and_encoding():
    report = official.parse_filing(filing().encode("cp950"), "2409", 2025)
    assert report["encoding"] == "cp950"
    extended = (filing() + b"\xfd\x40".decode("big5hkscs")).encode("big5hkscs")
    extended_report = official.parse_filing(extended, "2409", 2025)
    assert extended_report["encoding"] == "big5hkscs" and extended_report["records"][0]["value"] == 76_256_091_000
    assert official.parse_filing(b"\x80", "2409", 2025)["status"] == "invalid_data"
    assert report["records"][0]["value"] == 76_256_091_000
    assert all(row["value"] is None for row in report["records"][1:])
    assert report["equity_issued"] is None and report["can_screen"] is False
    assert official.parse_filing(filing("3481").encode(), "2409", 2025)["status"] == "invalid_data"
    assert official.parse_filing(filing().replace("Consolidated report", "Individual report").encode(), "2409", 2025)["status"] == "invalid_data"
    assert official.parse_filing(filing(unit="iso4217:USD").encode(), "2409", 2025)["records"][0]["value"] is None
    assert official.parse_filing(filing(amount="76,25,091").encode(), "2409", 2025)["records"][0]["value"] is None
    duplicate = '<ix:nonFraction name="ifrs-full:LongtermBorrowings" contextRef="now">1</ix:nonFraction>'
    assert official.parse_filing(filing(extra=duplicate).encode(), "2409", 2025)["records"][0]["status"] == "ambiguous_data"
    dimensioned = filing().replace('<xbrli:entity>', '<xbrli:entity><xbrldi:explicitMember>segment</xbrldi:explicitMember>')
    assert official.parse_filing(dimensioned.encode(), "2409", 2025)["records"][0]["status"] == "missing_data"


def test_persistent_cache_retains_versions_and_rejects_bad_documents(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cache.db")
    requests = []

    def fetch(*args, **kwargs):
        requests.append(args[0])
        return io.BytesIO(filing(amount=str(len(requests))).encode())

    monkeypatch.setattr(official, "urlopen", fetch)
    first = official.fetch_official_financials("2409", 2025)
    second = official.fetch_official_financials("2409", 2025)
    assert not first["cache_hit"] and second["cache_hit"] and len(requests) == 1
    refreshed = official.fetch_official_financials("2409", 2025, refresh=True)
    assert refreshed["sha256"] != first["sha256"]
    with closing(store._conn()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM official_filings").fetchone()[0] == 2
    monkeypatch.setattr(official, "urlopen", lambda *args, **kwargs: io.BytesIO(b"blocked"))
    bad = official.fetch_official_financials("3481", 2025)
    assert bad["status"] == "invalid_data"
    assert official.fetch_official_financials("3481", 2025)["cache_hit"] is False
    with closing(store._conn()) as conn:
        assert conn.execute("SELECT valid FROM official_filings WHERE ticker='3481'").fetchone()[0] == 0


def equity_filing(*, issue="420", change="420", closing="1420", extra="", member="tifrs-es:OrdinaryShareMember"):
    context = f'''<xbrli:context id="movement"><xbrli:entity>
    <xbrli:identifier>2409</xbrli:identifier></xbrli:entity><xbrli:period>
    <xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate>
    </xbrli:period><xbrli:scenario><xbrldi:explicitMember dimension="ifrs-full:ComponentsOfEquityAxis">
    {member}</xbrldi:explicitMember>{extra}</xbrli:scenario></xbrli:context>'''

    def fact(name, context, value):
        return f'''<ix:nonFraction name="{name}" contextRef="{context}" unitRef="money"
        format="ixt:numdotdecimal" scale="3">{value}</ix:nonFraction>'''

    content = context
    for key, instant, value in [("opening", "2025-01-01", "1000"), ("closing", "2025-12-31", closing)]:
        content += context.replace('id="movement"', f'id="{key}"').replace(
            '<xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate>',
            f'<xbrli:instant>{instant}</xbrli:instant>')
        content += fact("ifrs-full:Equity", key, value)
    content += fact("ifrs-full:ChangesInEquity", "movement", change)
    if issue is not None:
        content += fact("tifrs-es:IssueOfShares", "movement", issue)
    return filing(extra=content)


def test_ordinary_issuance_keeps_annual_evidence_and_does_not_infer_no_issue():
    report = official.parse_filing(equity_filing().encode(), "2409", 2025)
    current, previous = report["equity_evidence"]
    assert report["equity_issued"] is True and report["can_screen"] is False
    assert current["reconciled"] is True and current["opening"] == 1_000_000
    assert current["status"] == "extracted_unverified" and previous["status"] == "missing_data"
    assert any(r["tag"] == "tifrs-es:IssueOfShares" and r["value"] == 420_000 for r in current["records"])
    for issue in (None, "0"):
        report = official.parse_filing(equity_filing(issue=issue, change="0", closing="1000").encode(), "2409", 2025)
        assert report["equity_issued"] is None
        assert report["equity_evidence"][0]["reconciled"] is True
    # A retirement can offset issuance; unchanged closing capital cannot erase the event.
    report = official.parse_filing(equity_filing(change="0", closing="1000").encode(), "2409", 2025)
    assert report["equity_issued"] is True
    source = equity_filing().replace("2025-01-01", "2024-01-01").replace("2025-12-31", "2024-12-31")
    report = official.parse_filing(source.encode(), "2409", 2025)
    assert report["equity_issued"] is None and report["equity_evidence"][1]["equity_issued"] is True


def test_ordinary_issuance_rejects_ambiguous_invalid_and_other_scope():
    duplicate = '''<ix:nonFraction name="tifrs-es:IssueOfShares" contextRef="movement"
    unitRef="money" format="ixt:numdotdecimal" scale="3">420</ix:nonFraction>'''
    cases = [
        (equity_filing(closing="1000"), "needs_review"),
        (equity_filing(issue="4,20"), "invalid_data"),
        (equity_filing().replace("iso4217:TWD", "iso4217:USD"), "invalid_data"),
        (equity_filing() + duplicate, "ambiguous_data"),
        (equity_filing(member="ifrs-full:IssuedCapitalMember"), "missing_data"),
        (equity_filing(extra='<xbrldi:typedMember dimension="segment">x</xbrldi:typedMember>'), "missing_data"),
        (equity_filing(extra='<xbrldi:explicitMember dimension="segment">x</xbrldi:explicitMember>'), "missing_data"),
        (equity_filing().replace("2025-01-01", "2025-04-01"), "unverified"),
    ]
    for source, status in cases:
        report = official.parse_filing(source.encode(), "2409", 2025)
        assert report["equity_issued"] is None
        assert report["equity_evidence"][0]["status"] == status
    signed = equity_filing(issue="0", change="420", closing="580").replace(
        'name="ifrs-full:ChangesInEquity"', 'sign="-" name="ifrs-full:ChangesInEquity"')
    report = official.parse_filing(signed.encode(), "2409", 2025)
    assert report["equity_evidence"][0]["change"] == -420_000
    assert report["equity_evidence"][0]["reconciled"] is True


def test_route_validates_before_fetch_and_upstream_rate_limit_is_safe(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "cache.db")
    def blocked(*args, **kwargs):
        raise HTTPError("https://secret", 429, "secret", {}, None)

    monkeypatch.setattr(official, "urlopen", blocked)
    with pytest.raises(HTTPException) as invalid:
        main.get_official_financials("2409", 9999)
    assert invalid.value.status_code == 422
    with pytest.raises(HTTPException) as invalid:
        main.get_official_financials("../../bad", 2025)
    assert invalid.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        # Avoid a persisted cache from a previous real run.
        official.fetch_official_financials("2409", 2025, refresh=True)
    assert error.value.status_code == 503 and "secret" not in error.value.detail


def test_batch_groups_issues_reports_differences_and_stops_on_limit(monkeypatch, tmp_path):
    requested = []

    def fetch(url, **kwargs):
        requested.append(url)
        if "/3481/" in url:
            raise HTTPError(url, 503, "limit", {}, None)
        if "official-financials" in url:
            result = official.parse_filing(equity_filing().encode(), "2409", 2025)
            result["cache_hit"] = True
        else:
            result = {"ticker": "2409", "dataset": "TaiwanStockBalanceSheet", "records": [
                {"date": "2025-12-31", "type": "LongtermBorrowings", "value": 1}]}
        return io.BytesIO(json.dumps(result).encode())

    monkeypatch.setattr(batch, "urlopen", fetch)
    output = tmp_path / "results.jsonl"
    summary = batch.audit_batch(["2409", "3481", "1303"], 2025, output, delay=0)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert summary["companies"] == 2 and summary["remaining"] == ["1303"]
    assert summary["cache_hits"] == 1 and len(requested) == 3
    assert rows[0]["comparisons"][0]["status"] == "needs_review"
    assert rows[0]["equity_issued"] is True
    assert rows[0]["equity_evidence"][0]["reconciled"] is True
    assert all(row["can_screen"] is False for row in rows)
    assert any(group["field"] == "equity_issued" for group in summary["exceptions"])
    assert json.loads(output.with_suffix(".exceptions.json").read_text(encoding="utf-8")) == summary


def test_batch_stops_when_service_lacks_route(monkeypatch, tmp_path):
    def outdated(url, **kwargs):
        raise HTTPError(url, 404, "Not Found", {}, io.BytesIO(b'{"detail":"Not Found"}'))

    monkeypatch.setattr(batch, "urlopen", outdated)
    summary = batch.audit_batch(["2409", "3481"], 2025, tmp_path / "old.jsonl", delay=0)
    assert summary["companies"] == 1 and summary["remaining"] == ["3481"]
    assert summary["exceptions"][0]["status"] == "service_outdated"
