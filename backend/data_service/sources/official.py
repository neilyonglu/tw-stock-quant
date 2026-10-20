"""官方年度合併財報原始文件及有限科目查核；不推定缺值為零。"""

import hashlib
import re
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from backend.data_service import store

FIELDS = {
    "noncurrent_borrowings": "ifrs-full:LongtermBorrowings",
    "noncurrent_bonds": "ifrs-full:NoncurrentPortionOfNoncurrentBondsIssued",
    "noncurrent_leases": "ifrs-full:NoncurrentFinanceLeaseLiabilities",
}
_LEAVES = {"xbrli:identifier", "xbrli:instant", "xbrli:measure"}
_METADATA = {"tifrs-notes:CompanyID", "tifrs-notes:Year", "tifrs-notes:ReportCategory"}


class _Filing(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.contexts, self.units, self.facts, self.metadata = {}, {}, [], {}
        self.context = self.unit = self.fact = self.leaf = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "xbrli:context":
            self.context = {"id": attrs.get("id"), "dimensioned": False}
        elif tag == "xbrli:unit":
            self.unit = {"id": attrs.get("id"), "measures": [], "divided": False}
        elif tag == "xbrli:divide" and self.unit is not None:
            self.unit["divided"] = True
        elif tag in ("xbrldi:explicitmember", "xbrldi:typedmember") and self.context is not None:
            self.context["dimensioned"] = True
        elif tag in _LEAVES:
            self.leaf = [tag, ""]
        elif tag == "ix:nonfraction" and attrs.get("name") in FIELDS.values():
            self.fact = [tag, attrs, ""]
        elif tag == "ix:nonnumeric" and attrs.get("name") in _METADATA:
            self.fact = [tag, attrs, ""]

    def handle_data(self, data):
        if self.leaf is not None:
            self.leaf[1] += data
        if self.fact is not None:
            self.fact[2] += data

    def handle_endtag(self, tag):
        if self.leaf is not None and tag == self.leaf[0]:
            value = self.leaf[1].strip()
            if tag == "xbrli:measure" and self.unit is not None:
                self.unit["measures"].append(value)
            elif self.context is not None:
                self.context[tag.split(":")[1]] = value
            self.leaf = None
        if tag == "xbrli:context" and self.context is not None:
            key = self.context["id"]
            if not key or key in self.contexts:
                raise ValueError("報表期間識別碼重複或缺少")
            self.contexts[key] = self.context
            self.context = None
        elif tag == "xbrli:unit" and self.unit is not None:
            key = self.unit["id"]
            if not key or key in self.units:
                raise ValueError("報表單位識別碼重複或缺少")
            self.units[key] = self.unit
            self.unit = None
        elif self.fact is not None and tag == self.fact[0]:
            _, attrs, value = self.fact
            if tag == "ix:nonnumeric":
                self.metadata.setdefault(attrs["name"], set()).add(value.strip())
            else:
                self.facts.append((attrs, value.strip()))
            self.fact = None


def parse_filing(raw: bytes, ticker: str, year: int) -> dict:
    """純解析：只接受指定公司／年度／合併範圍、無維度的期末TWD事實。"""
    report = {"ticker": ticker, "filing_year": year, "status": "invalid_data", "records": [],
              "equity_issued": None, "can_screen": False, "issues": []}
    try:
        try:
            text = raw.decode("utf-8-sig")
            encoding = "utf-8"
        except UnicodeDecodeError:
            try:
                text = raw.decode("cp950")
                encoding = "cp950"
            except UnicodeDecodeError:
                text = raw.decode("big5hkscs")
                encoding = "big5hkscs"
        parser = _Filing()
        parser.feed(text)
        parser.close()
        for name, expected in [("tifrs-notes:CompanyID", ticker), ("tifrs-notes:Year", str(year)),
                               ("tifrs-notes:ReportCategory", "Consolidated report")]:
            if parser.metadata.get(name) != {expected}:
                raise ValueError("公司、年度或合併報表範圍無法確認")
        for period in (f"{year}-12-31", f"{year - 1}-12-31"):
            for field, tag in FIELDS.items():
                matches = []
                for attrs, text_value in parser.facts:
                    context = parser.contexts.get(attrs.get("contextref"), {})
                    if (attrs["name"] == tag and context.get("identifier") == ticker
                            and context.get("instant") == period and not context.get("dimensioned", True)):
                        matches.append((attrs, text_value))
                record = {"period": period, "field": field, "tag": tag, "value": None,
                          "status": "missing_data", "unit": "TWD"}
                if len(matches) > 1:
                    record["status"] = "ambiguous_data"
                elif matches:
                    attrs, value = matches[0]
                    unit = parser.units.get(attrs.get("unitref"), {})
                    try:
                        if (unit.get("measures") != ["iso4217:TWD"] or unit.get("divided", True)
                                or attrs.get("format") not in ("ixt:numdotdecimal", "ixt:num-dot-decimal")
                                or attrs.get("xsi:nil") in ("true", "1") or attrs.get("sign")
                                or not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", value)):
                            raise ValueError
                        scale = int(attrs.get("scale", "0"))
                        if not -9 <= scale <= 9:
                            raise ValueError
                        amount = Decimal(value.replace(",", "")) * Decimal(10) ** scale
                        if amount != amount.to_integral_value():
                            raise ValueError
                        record.update(value=int(amount), status="extracted_unverified")
                    except (ValueError, ArithmeticError):
                        record["status"] = "invalid_data"
                report["records"].append(record)
                if record["status"] != "extracted_unverified":
                    report["issues"].append({"period": period, "field": field, "status": record["status"]})
        report.update(status="partial", encoding=encoding)
        report["issues"].append({"period": f"{year}-12-31", "field": "equity_issued",
                                 "status": "unverified", "reason": "尚未驗證可跨公司判斷普通股發行事件的規則"})
    except (ValueError, UnicodeError) as error:
        report["issues"] = [{"field": "document", "status": "invalid_data", "reason": str(error)}]
    return report


def fetch_official_financials(ticker: str, year: int, refresh: bool = False) -> dict:
    """內容以SHA保存版本；有效文件24小時內不重抓，仍逐次執行目前解析規則。"""
    now = datetime.now(UTC)
    url = "https://mopsov.twse.com.tw/server-java/t164sb01?" + urlencode(
        {"step": 1, "CO_ID": ticker, "SYEAR": year, "SSEASON": 4, "REPORT_ID": "C"})
    with closing(store._conn()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS official_filings (
            ticker TEXT, year INTEGER, sha256 TEXT, fetched_at TEXT, valid INTEGER, raw BLOB,
            PRIMARY KEY (ticker, year, sha256))""")
        cached = conn.execute("""SELECT fetched_at, raw, valid FROM official_filings
            WHERE ticker=? AND year=? ORDER BY fetched_at DESC LIMIT 1""", (ticker, year)).fetchone()
    cache_hit = bool(not refresh and cached and cached[2] and (now - datetime.fromisoformat(cached[0])).total_seconds() < 86400)
    if cache_hit:
        fetched_at, raw, _ = cached
    else:
        try:
            with urlopen(Request(url, headers={"User-Agent": "tw-stock-quant"}), timeout=30) as response:
                raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise HTTPException(502, "官方報表超過10MB讀取上限")
        except HTTPError as error:
            raise HTTPException(503 if error.code in (403, 429, 503) else 502, "官方來源暫時無法提供資料；不自動重試") from None
        except TimeoutError:
            raise HTTPException(504, "官方來源請求逾時") from None
        except (URLError, OSError):
            raise HTTPException(502, "無法取得官方報表") from None
        fetched_at = now.isoformat()
    report = parse_filing(raw, ticker, year)
    digest = hashlib.sha256(raw).hexdigest()
    if not cache_hit:
        with closing(store._conn()) as conn, conn:
            conn.execute("""INSERT INTO official_filings VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, year, sha256) DO UPDATE SET fetched_at=excluded.fetched_at, valid=excluded.valid""",
                         (ticker, year, digest, fetched_at, report["status"] != "invalid_data", raw))
    report.update(source="MOPS", source_url=url, fetched_at=fetched_at, sha256=digest, cache_hit=cache_hit)
    return report
