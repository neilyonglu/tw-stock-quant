"""Offline runtime check: uv run python -m scripts.check_announcements."""

import copy
import io
import json
from datetime import date
from unittest.mock import patch
from urllib.error import URLError

from backend.data_service.sources import announcements, fundamental
from backend.screening import fundamental_quality
from backend.screening.fundamental import evaluate_fundamental
from backend.screening.fundamental_quality import assess_fundamentals

# Source text and URLs checked against TSMC's latest-news page on 2026-10-22.
NEWS = """<a href="/english/news/3346"><span>2026/10/15</span>
TSMC Reports Third Quarter EPS of NT$29.43</a>
<a href="/english/news/3343">2026/10/08
<span>TSMC September 2026 Revenue Report</span></a>
<a href="https://example.invalid/english/news/1">2026/10/20
TSMC October 2026 Revenue Report</a>"""
RELEASE = """<div>Issued on:</div><time>2026/10/15</time>
<p>for the third quarter ended September 30, 2026.</p>"""
INNOLUX = {"years": [2026, 2025], "totalCount": 3, "list": [
    {"id": 2468, "news_date": "2026-10-12", "title": "Innolux Corporation (3481.TW) announced unaudited consolidated revenue of NT$20.0 billion for September 2026"},
    {"id": 2451, "news_date": "2026-08-14", "title": "Innolux Corporation Reports Second Quarter 2026 Financial Results"},
    {"id": 2455, "news_date": "2026-08-18", "title": "Innolux Targets the New Blue Ocean of Glass Substrates "},
]}


def main():
    for fetch in (announcements._fetch_page, announcements.fetch_announcements, fundamental.fetch_fundamentals):
        fetch.cache_clear()
    calls = []

    def source(request, timeout):
        calls.append(request.full_url)
        assert timeout == 5
        return io.BytesIO((NEWS if request.full_url == announcements.NEWS_URL else RELEASE).encode())

    with patch.object(announcements, "urlopen", source):
        monthly = announcements.fetch_announcements("2330", "TaiwanStockMonthRevenue")
        earnings = announcements.fetch_announcements("2330", "TaiwanStockFinancialStatements")
        assert announcements.fetch_announcements("2330", "TaiwanStockMonthRevenue") == monthly
        assert announcements.fetch_announcements("2317", "TaiwanStockMonthRevenue")["status"] == "unsupported"
        assert announcements.fetch_announcements("2330", "TaiwanStockBalanceSheet")["status"] == "unsupported"
    assert len(calls) == 2
    assert monthly["records"][0]["published_on"] == "2026-10-08"
    assert monthly["records"][0]["period"] == "2026-09-01"
    assert earnings["records"][0]["period"] == "2026-09-30"
    assert earnings["records"][0]["source_kind"] == "earnings_release"
    rows = [{"stock_id": "2330", "date": "2026-09-01", "revenue_year": 2026,
             "revenue_month": 8, "revenue": None}]
    with patch.object(fundamental, "urlopen", return_value=io.BytesIO(json.dumps({"status": 200, "data": rows}).encode())):
        raw = fundamental.fetch_fundamentals("2330", "monthly_revenue", date(2026, 1, 1), date(2026, 10, 22))
    original = copy.deepcopy(raw)
    quality = assess_fundamentals(raw)
    assert raw == original and raw["records"] == rows
    assert quality["status"] == "pending_update" and quality["can_screen"] is False
    history = [{"stock_id": "2330", "date": date(year, month + 1, 1).isoformat(),
                "revenue_year": year, "revenue_month": month, "revenue": 100}
               for year in (2025, 2026) for month in (6, 7, 8) if (year, month) != (2026, 8)]
    screening = evaluate_fundamental({"monthly_revenue": {
        **raw, "start_date": "2025-01-01", "records": history + rows}}, industry="半導體業")
    rule = next(item for item in screening["rules"] if item["id"] == "revenue_yoy_three_months")
    assert rule["status"] == "pending_update" and rule["condition_met"] is None
    raw["end_date"] = "2026-10-07"
    assert assess_fundamentals(raw)["status"] == "unverified"
    raw["end_date"] = "2026-10-08"
    assert assess_fundamentals(raw)["status"] == "pending_update"
    raw["records"] = [{**rows[0], "date": "2026-10-01", "revenue_month": 9, "revenue": 0}]
    quality = assess_fundamentals(raw)
    assert quality["status"] == "unverified" and quality["can_screen"] is None
    raw.update(dataset="TaiwanStockFinancialStatements", announcement_tracking=earnings,
               records=[{"stock_id": "2330", "date": "2026-06-30", "type": "EPS", "value": None}],
               end_date="2026-10-22")
    with patch.dict(fundamental_quality._REFERENCES, {"announcements": []}):
        quality = assess_fundamentals(raw)
        assert quality["status"] == "pending_update" and quality["can_screen"] is False
        assert quality["latest_announcement"]["source_kind"] == "earnings_release"
        raw["end_date"] = "2026-10-14"
        assert "latest_announcement" not in assess_fundamentals(raw)
    raw.update(dataset="TaiwanStockFinancialStatements", announcement_tracking=earnings,
               start_date="2026-07-01", end_date="2026-10-22",
               records=[{"stock_id": "2330", "date": "2026-09-30", "type": "EPS", "value": None}])
    quality = assess_fundamentals(raw)
    assert quality["can_screen"] is None and quality["status"] == "unverified"
    assert quality["reviewed_announcement"]["source_url"].startswith("https://www.sec.gov/")
    for fetch in (announcements._fetch_page, announcements.fetch_announcements):
        fetch.cache_clear()
    with patch.object(announcements, "urlopen", side_effect=URLError("private")):
        failed = announcements.fetch_announcements("2330", "TaiwanStockFinancialStatements")
    assert failed["status"] == "source_error" and "private" not in json.dumps(failed)
    raw["announcement_tracking"] = failed
    quality = assess_fundamentals(raw)
    assert quality["status"] == "unverified" and quality["can_screen"] is False
    raw["announcement_tracking"] = []
    assert assess_fundamentals(raw)["status"] == "invalid_data"
    try:
        announcements.parse_earnings_period(RELEASE.replace("September 30", "September 29"), "2026-10-15")
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid quarter end accepted")
    check_other_issuers()
    check_innolux_and_read_limit()
    print("PASS: parser, cache/raw client, publication cutoff, quality, nulls, manual references, source failure")


def check_other_issuers():
    """Small HTML fixtures model official list markup; no network is used."""
    stamp = "2026-10-22T00:00:00+00:00"
    auo = '<a href="/en-global/New_Archive/detail/News_Archive_FinanceReport_20261008">2026-10-08 AUO Corporation Reports September 2026 Consolidated Revenue</a><a href="/en-global/New_Archive/detail/news_IR_20260730">2026-07-30 AUO Corporation Reports Second Quarter 2026 Financial Results</a>'
    gwc = '<a href="/en/gwc_news_en_20261007/">2026/10/07</a><a href="/en/gwc_news_en_20261007/">SAS &amp; GWC September 2026 Revenue Report</a><a href="/en/gwc_news_en_20260804/">2026/08/04</a><a href="/en/gwc_news_en_20260804/">GlobalWafers Reports Q2 2026 Results</a>'
    bodies = {
        "https://www.sas-globalwafers.com/en/gwc_news_en_20261007/": "GlobalWafers (GWC, 6488:TT), also released its September results today.",
        "https://www.sas-globalwafers.com/en/gwc_news_en_20260804/": "GlobalWafers Co., Ltd. (6488) approved its financial statements for the second quarter ended June 30, 2026.",
    }
    pages = {announcements.SOURCES["2409"][1]: auo, announcements.SOURCES["6488"][1]: gwc,
             announcements.SOURCES["3481"][1]: json.dumps(INNOLUX), **bodies}
    with patch.object(announcements, "_fetch_page", side_effect=lambda url: (pages[url], stamp)):
        for ticker, publication in (("2409", "2026-10-08"), ("6488", "2026-10-07"), ("3481", "2026-10-12")):
            for dataset, period in (("TaiwanStockMonthRevenue", "2026-09-01"),
                                    ("TaiwanStockFinancialStatements", "2026-06-30")):
                announcements.fetch_announcements.cache_clear()
                report = announcements.fetch_announcements(ticker, dataset)
                assert report["status"] == "available", report
                item = report["records"][0]
                assert item["period"] == period
                assert item["source_kind"] == announcements.DATASETS[dataset]
                raw = {"ticker": ticker, "dataset": dataset, "source": "FinMind", "fetched_at": stamp,
                       "start_date": "2026-01-01", "end_date": "2026-10-22", "announcement_tracking": report,
                       "records": [{"stock_id": ticker, "date": "2026-09-01", "revenue_year": 2026,
                                    "revenue_month": 8, "revenue": None}] if dataset == "TaiwanStockMonthRevenue" else
                                  [{"stock_id": ticker, "date": "2026-03-31", "type": "EPS", "value": None}]}
                original = copy.deepcopy(raw)
                with patch.dict(fundamental_quality._REFERENCES, {"announcements": [], "comparisons": []}):
                    quality = assess_fundamentals(raw)
                    assert quality["status"] == "pending_update" and quality["can_screen"] is False
                    assert raw == original
                    raw["end_date"] = date.fromordinal(date.fromisoformat(item["published_on"]).toordinal()-1).isoformat()
                    assert assess_fundamentals(raw)["status"] == "unverified"
                    raw["end_date"] = item["published_on"]
                    assert assess_fundamentals(raw)["status"] == "pending_update"
                    for field, value in (("ticker", "5483"), ("source_url", "https://example.invalid/"),
                                         ("source_url", "https://pr.tsmc.com/english/news/3346"),
                                         ("title", "OtherIssuer " + item["title"]),
                                         ("source_kind", "reviewed_financial_statement"), ("period", "2026-12-31")):
                        bad = copy.deepcopy(raw)
                        bad["announcement_tracking"]["records"][0][field] = value
                        assert assess_fundamentals(bad)["status"] == "invalid_data", (ticker, field)
                    current = copy.deepcopy(raw)
                    current["records"][0]["date"] = period
                    if dataset == "TaiwanStockMonthRevenue":
                        current["records"][0]["revenue_month"] = 9
                    quality = assess_fundamentals(current)
                    assert quality["status"] == "unverified" and quality["can_screen"] is None
                    raw["records"] = []
                    assert assess_fundamentals(raw)["status"] == "missing_data"
                if dataset == "TaiwanStockMonthRevenue":
                    assert item["published_on"] == publication
    for ticker in ("2409", "6488", "3481"):
        empty = '{"list": []}' if ticker == "3481" else "<html>No dated releases</html>"
        for html, expected in ((empty, "unavailable"),):
            announcements.fetch_announcements.cache_clear()
            with patch.object(announcements, "_fetch_page", return_value=(html, stamp)):
                assert announcements.fetch_announcements(ticker, "TaiwanStockMonthRevenue")["status"] == expected
        announcements.fetch_announcements.cache_clear()
        with patch.object(announcements, "_fetch_page", side_effect=URLError("private")):
            failure = announcements.fetch_announcements(ticker, "TaiwanStockMonthRevenue")
            assert failure["status"] == "source_error" and not failure["records"]
        raw = {"ticker": ticker, "dataset": "TaiwanStockMonthRevenue", "source": "FinMind",
               "fetched_at": stamp, "start_date": "2026-01-01", "end_date": "2026-10-22",
               "announcement_tracking": failure,
               "records": [{"stock_id": ticker, "date": "2026-10-01", "revenue_year": 2026,
                            "revenue_month": 9, "revenue": None}]}
        with patch.dict(fundamental_quality._REFERENCES, {"announcements": [], "comparisons": []}):
            quality = assess_fundamentals(raw)
            assert quality["status"] == "unverified" and quality["can_screen"] is False
    for body in ("SAS (5483:TT) released its September results today.",
                 bodies[next(iter(bodies))].replace("September", "August")):
        try:
            announcements._confirm_gwc(body, {"period": "2026-09-01", "source_kind": "monthly_revenue_announcement"})
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong issuer/period accepted as GlobalWafers")
    q1 = {"period": "2026-03-31", "source_kind": "earnings_release"}
    announcements._confirm_gwc("GlobalWafers held its board meeting today (May 5, 2026) to approve its financial "
                               "statements for the first quarter ended on March 31, 2026 with revenue", q1)
    for body in ("GlobalWafers held its board meeting to approve its financial statements for the second quarter ended on March 31, 2026",
                 "SAS (5483:TT) approved its financial statements for the first quarter ended on March 31, 2026",
                 "GlobalWafers held its board meeting. SAS approved its financial statements for the first quarter ended on March 31, 2026"):
        try:
            announcements._confirm_gwc(body, q1)
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong issuer/quarter accepted as GlobalWafers earnings")
    undated = announcements.parse_company_news(auo.replace("2026-10-08 AUO", "AUO"), stamp, "2409")
    assert all(row["dataset"] != "TaiwanStockMonthRevenue" for row in undated)
    print("PASS: AUO/GWC/Innolux issuer, date cutoff, wrong source/issuer, missing/null and failures")


def check_innolux_and_read_limit():
    stamp = "2026-10-22T00:00:00+00:00"
    malformed = ["not json", "null", "[]", "{}", '{"list": null}', '{"list": {}}', '{"list": [null]}']
    for field, values in (("id", (None, True, 0, -1, "2468", 2468.5)),
                          ("title", (None, 42)), ("news_date", (None, 42, "invalid", "2026-09-30"))):
        for value in values:
            malformed.append(json.dumps({"list": [{**INNOLUX["list"][0], field: value}]}))
    for payload in malformed:
        announcements.fetch_announcements.cache_clear()
        with patch.object(announcements, "_fetch_page", return_value=(payload, stamp)):
            report = announcements.fetch_announcements("3481", "TaiwanStockMonthRevenue")
        assert report["status"] == "source_error" and not report["records"], payload
    for title in (INNOLUX["list"][0]["title"].replace("3481.TW", "2409.TW"),
                  INNOLUX["list"][1]["title"].replace("Innolux", "AUO")):
        assert announcements.parse_innolux_news(json.dumps({"list": [
            {**INNOLUX["list"][0], "title": title}]}), stamp) == []
    item = announcements.parse_innolux_news(json.dumps(INNOLUX), stamp)[0]
    assert item["source_url"] == "https://www.innolux.com/en/media_center/news_list/news.html?p=2468"
    for url in (item["source_url"] + "&lang=EN", item["source_url"] + "#fragment",
                item["source_url"].replace("p=2468", "p=0"), item["source_url"] + "&p=2451"):
        bad = {**item, "source_url": url}
        assert not announcements.valid_source("3481", bad)
    rollover = {**INNOLUX["list"][0], "news_date": "2027-01-12",
                "title": INNOLUX["list"][0]["title"].replace("September", "December")}
    assert announcements.parse_innolux_news(json.dumps({"list": [rollover]}), stamp)[0]["period"] == "2026-12-01"
    assert announcements.SOURCES["3481"][1].endswith("lang=EN&pageIndex=0&dept=ir&year=")

    class BoundedPage(io.BytesIO):
        def read(self, size=-1):
            assert size == 4_000_001
            return super().read(size)

    for size in (3_398_835, 4_000_000, 4_000_001):
        announcements._fetch_page.cache_clear()
        with patch.object(announcements, "urlopen", return_value=BoundedPage(b"x" * size)) as opened:
            try:
                text, _ = announcements._fetch_page(announcements.SOURCES["6488"][1])
                assert size <= 4_000_000 and len(text) == size
            except ValueError:
                assert size > 4_000_000
            assert opened.call_args.kwargs["timeout"] == 5
    announcements._fetch_page.cache_clear()
    announcements.fetch_announcements.cache_clear()
    with patch.object(announcements, "urlopen", return_value=BoundedPage(b"x" * 4_000_001)):
        assert announcements.fetch_announcements("6488", "TaiwanStockMonthRevenue")["status"] == "source_error"
    print("PASS: Innolux API shape, null dates, source identity, rollover and bounded 4,000,000-byte reads")


if __name__ == "__main__":
    main()
