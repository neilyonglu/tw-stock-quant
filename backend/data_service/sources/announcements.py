"""Recent official issuer press releases, kept separate from reviewed financial statements."""

import json
import re
from calendar import monthrange
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from backend.data_service.cache import ttl_cache

NEWS_URL = "https://pr.tsmc.com/english/latest-news"
SOURCES = {
    "2330": ("TSMC", NEWS_URL, r"https://pr\.tsmc\.com/english/news/\d+"),
    "2409": ("AUO", "https://www.auo.com/en-global/New_Archive/index",
             r"https://(?:www\.)?auo\.com/en-global/New_Archive/detail/(?:News_Archive_FinanceReport_|news_IR_)\d{8}"),
    "6488": ("GlobalWafers", "https://www.sas-globalwafers.com/en/category/news_en/",
             r"https://www\.sas-globalwafers\.com/en/gwc_news_en_\d{8}/"),
    "3481": ("Innolux", "https://www.innolux.com/api/news/GetNewsList?" + urlencode(
        {"lang": "EN", "pageIndex": 0, "dept": "ir", "year": ""}),
        r"https://www\.innolux\.com/en/media_center/news_list/news\.html\?p=[1-9]\d*"),
}
DATASETS = {"TaiwanStockFinancialStatements": "earnings_release",
            "TaiwanStockMonthRevenue": "monthly_revenue_announcement"}
_MONTHS = "January February March April May June July August September October November December".split()
_QUARTERS = {"first": 3, "second": 6, "third": 9, "fourth": 12}


class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.text = [], []
        self.link = None
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag == "a":
            self.link = [dict(attrs).get("href", ""), []]

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)
            if self.link is not None:
                self.link[1].append(data)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
        if tag == "a" and self.link is not None:
            href, parts = self.link
            self.links.append((href, " ".join(" ".join(parts).split())))
            self.link = None


def parse_news(html: str, fetched_at: str) -> list[dict]:
    """Read dated release links; earnings periods require the release body."""
    page = _Page()
    page.feed(html)
    page.close()
    records = {}
    for href, text in page.links:
        url = urljoin(NEWS_URL, href)
        if not re.fullmatch(r"https://pr\.tsmc\.com/english/news/\d+", url):
            continue
        match = re.fullmatch(r"(\d{4}/\d{2}/\d{2})\s+(TSMC .+)", text)
        if not match:
            continue
        published = date.fromisoformat(match[1].replace("/", "-"))
        title = match[2]
        monthly = re.fullmatch(r"TSMC (\w+) (\d{4}) Revenue Report", title)
        if monthly and monthly[1] in _MONTHS:
            period = date(int(monthly[2]), _MONTHS.index(monthly[1]) + 1, 1)
            if period.replace(day=monthrange(period.year, period.month)[1]) >= published:
                raise ValueError("Revenue announcement precedes the reporting month end")
            dataset, kind = "TaiwanStockMonthRevenue", "monthly_revenue_announcement"
        elif re.match(r"TSMC Reports (First|Second|Third|Fourth) Quarter\b", title):
            period = None
            dataset, kind = "TaiwanStockFinancialStatements", "earnings_release"
        else:
            continue
        records[url] = {"ticker": "2330", "dataset": dataset, "source_kind": kind,
                        "period": period.isoformat() if period else None,
                        "published_on": published.isoformat(), "source_url": url,
                        "fetched_at": fetched_at, "title": title}
    return sorted(records.values(), key=lambda row: row["published_on"], reverse=True)


def parse_earnings_period(html: str, published_on: str) -> str:
    page = _Page()
    page.feed(html)
    page.close()
    text = " ".join(" ".join(page.text).split())
    if not re.search(r"Issued on:\s*" + re.escape(published_on.replace("-", "/")), text):
        raise ValueError("Release publication date could not be confirmed")
    periods = set()
    for quarter, month, day, year in re.findall(
        r"for the (first|second|third|fourth) quarter ended (\w+) (\d{1,2}), (\d{4})", text, re.I
    ):
        if month.capitalize() not in _MONTHS:
            raise ValueError("Unknown reporting month")
        period = date(int(year), _MONTHS.index(month.capitalize()) + 1, int(day))
        if (period.month != _QUARTERS[quarter.lower()]
                or period.day != monthrange(period.year, period.month)[1]
                or period >= date.fromisoformat(published_on)):
            raise ValueError("Invalid earnings reporting period")
        periods.add(period.isoformat())
    if len(periods) != 1:
        raise ValueError("Earnings reporting period could not be confirmed")
    return periods.pop()


@ttl_cache(seconds=1800)
def _fetch_page(url: str) -> tuple[str, str]:
    with urlopen(Request(url, headers={"User-Agent": "tw-stock-quant"}), timeout=5) as response:
        raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ValueError("Announcement page exceeds 4,000,000 bytes")
    return raw.decode("utf-8-sig"), datetime.now(UTC).isoformat()


def _title_period(ticker: str, title: str) -> tuple[str, str] | None:
    if not isinstance(title, str):
        return None
    if ticker == "2409":
        monthly = re.fullmatch(r"AUO Corporation Reports (\w+) (\d{4}) Consolidated Revenue", title)
        earnings = re.fullmatch(r"AUO Corporation Reports (First|Second|Third|Fourth) Quarter (\d{4}) Financial Results", title)
    elif ticker == "3481":
        monthly = re.fullmatch(r"Innolux Corporation \(3481\.TW\) announced unaudited consolidated revenue of NT\$\s*\d+(?:\.\d+)? billion for (\w+) (\d{4})", title)
        earnings = re.fullmatch(r"Innolux Corporation Reports (First|Second|Third|Fourth) Quarter (\d{4}) Financial Results", title)
    else:
        monthly = re.fullmatch(r"SAS & GWC (\w+) (\d{4}) Revenue Report", title)
        earnings = re.fullmatch(r"GlobalWafers Reports Q([1-4]) (\d{4}) Results", title)
    if monthly and monthly[1] in _MONTHS:
        return "TaiwanStockMonthRevenue", date(int(monthly[2]), _MONTHS.index(monthly[1]) + 1, 1).isoformat()
    if earnings:
        month = int(earnings[1]) * 3 if ticker == "6488" else _QUARTERS[earnings[1].lower()]
        year = int(earnings[2])
        return "TaiwanStockFinancialStatements", date(year, month, monthrange(year, month)[1]).isoformat()
    return None


def valid_source(ticker: str, item: dict) -> bool:
    """Keep the issuer allowlist shared by retrieval and the quality boundary."""
    source = SOURCES.get(ticker)
    url = item.get("source_url")
    if not source or not source[2] or not isinstance(url, str) or not re.fullmatch(source[2], url):
        return False
    if ticker == "2330":
        return True
    classified = _title_period(ticker, item.get("title", ""))
    return (classified is not None and classified == (item.get("dataset"), item.get("period"))
            and (ticker == "3481" or item.get("published_on", "").replace("-", "")
                 == re.search(r"(\d{8})/?$", url)[1]))


def parse_innolux_news(payload: str, fetched_at: str) -> list[dict]:
    feed = json.loads(payload)
    if not isinstance(feed, dict) or not isinstance(feed.get("list"), list):
        raise ValueError("Invalid Innolux news response")
    records = []
    for item in feed["list"]:
        if (not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] <= 0
                or not isinstance(item.get("title"), str) or not isinstance(item.get("news_date"), str)):
            raise ValueError("Invalid Innolux news item")
        published = date.fromisoformat(item["news_date"])
        classified = _title_period("3481", item["title"])
        if not classified:
            continue
        dataset, period = classified
        period_end = date.fromisoformat(period)
        if dataset == "TaiwanStockMonthRevenue":
            period_end = period_end.replace(day=monthrange(period_end.year, period_end.month)[1])
        if period_end >= published:
            raise ValueError("Announcement precedes reporting period end")
        records.append({"ticker": "3481", "dataset": dataset, "source_kind": DATASETS[dataset],
                        "period": period, "published_on": published.isoformat(),
                        "source_url": "https://www.innolux.com/en/media_center/news_list/news.html?"
                                      + urlencode({"p": item["id"]}),
                        "fetched_at": fetched_at, "title": item["title"]})
    return sorted(records, key=lambda row: row["published_on"], reverse=True)


def parse_company_news(html: str, fetched_at: str, ticker: str) -> list[dict]:
    page = _Page()
    page.feed(html)
    page.close()
    # GlobalWafers uses separate date and title anchors pointing to the same article.
    links = {}
    for href, text in page.links:
        url = urljoin(SOURCES[ticker][1], href)
        if re.fullmatch(SOURCES[ticker][2], url):
            if text:
                links.setdefault(url, []).append(text)
    records = []
    for url, parts in links.items():
        text = " ".join(dict.fromkeys(parts))
        match = re.fullmatch(r"(\d{4}[-/]\d{2}[-/]\d{2})\s+(.+)", text)
        if not match:
            continue
        published, title = match[1].replace("/", "-"), match[2]
        date.fromisoformat(published)
        classified = _title_period(ticker, title)
        if not classified:
            continue
        dataset, period = classified
        period_end = date.fromisoformat(period)
        if dataset == "TaiwanStockMonthRevenue":
            period_end = period_end.replace(day=monthrange(period_end.year, period_end.month)[1])
        if period_end >= date.fromisoformat(published):
            raise ValueError("Announcement precedes reporting period end")
        row = {"ticker": ticker, "dataset": dataset, "source_kind": DATASETS[dataset],
               "period": period, "published_on": published, "source_url": url,
               "fetched_at": fetched_at, "title": title}
        if not valid_source(ticker, row):
            raise ValueError("Issuer publication date and article URL disagree")
        records.append(row)
    return sorted(records, key=lambda row: row["published_on"], reverse=True)


def _confirm_gwc(html: str, row: dict) -> None:
    page = _Page()
    page.feed(html)
    text = " ".join(" ".join(page.text).split())
    if row["source_kind"] == "monthly_revenue_announcement":
        month = _MONTHS[date.fromisoformat(row["period"]).month - 1]
        pattern = r"GlobalWafers \(GWC, 6488:TT\), also released its " + month + r" results today"
    else:
        # Q2 names "GlobalWafers Co., Ltd. (6488)"; Q1 only "GlobalWafers held its board meeting ... ended on".
        period = date.fromisoformat(row["period"])
        ordinal = next(name for name, month in _QUARTERS.items() if month == period.month)
        pattern = (r"GlobalWafers(?: Co\., Ltd\. \(6488\))?[^.;]*?financial statements for the "
                   + ordinal + r" quarter ended (?:on )?"
                   + re.escape(f"{_MONTHS[period.month - 1]} {period.day}, {period.year}"))
    if not re.search(pattern, text, re.I):
        raise ValueError("GlobalWafers issuer and reporting period could not be confirmed")


@ttl_cache(seconds=1800)
def fetch_announcements(ticker: str, dataset: str) -> dict:
    source, news_url, _ = SOURCES.get(ticker, (None, None, None))
    report = {"ticker": ticker, "dataset": dataset, "source": source,
              "source_url": news_url, "fetched_at": None, "records": [],
              "status": "unsupported", "can_screen": False,
              "coverage": "Recent news page only; no historical completeness or reviewed filings"}
    if ticker not in SOURCES or dataset not in DATASETS:
        report["reason"] = "Automatic coverage supports selected issuer earnings releases and monthly revenue only"
        return report
    try:
        html, fetched_at = _fetch_page(news_url)
        report["fetched_at"] = fetched_at
        if ticker == "3481":
            parsed = parse_innolux_news(html, fetched_at)
        else:
            parsed = parse_news(html, fetched_at) if ticker == "2330" else parse_company_news(html, fetched_at, ticker)
        links = [row for row in parsed if row["dataset"] == dataset]
        # ponytail: recent-page window only; use archives if historical coverage is required.
        for row in links[:2 if dataset == "TaiwanStockFinancialStatements" else 4]:
            if ticker == "2330" and row["source_kind"] == "earnings_release":
                body, release_fetched_at = _fetch_page(row["source_url"])
                row = {**row, "period": parse_earnings_period(body, row["published_on"]),
                       "fetched_at": release_fetched_at}
            elif ticker == "6488":
                body, release_fetched_at = _fetch_page(row["source_url"])
                _confirm_gwc(body, row)
                row = {**row, "fetched_at": release_fetched_at}
            if row["source_kind"] == "earnings_release":
                row = {**row, "note": "Earnings release, not a complete reviewed financial statement"}
            report["records"].append(row)
        report["status"] = "available" if report["records"] else "unavailable"
        if not report["records"]:
            report["reason"] = "No recognized dated releases in the recent news window"
    except (OSError, ValueError, UnicodeError):
        report.update(status="source_error", reason="Official announcement retrieval or parsing failed")
    return report
