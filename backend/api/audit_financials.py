"""批次官方財報查核；只經中台取資料，JSONL保留每家公司結果，例外按規則分組。"""

import argparse
import json
import os
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from backend.data.universe import stock_universe


def compare_finmind(report: dict, raw: dict) -> None:
    if raw.get("ticker") != report["ticker"] or raw.get("dataset") != "TaiwanStockBalanceSheet" or not isinstance(raw.get("records"), list):
        raise ValueError("中台回傳的股票或報表不符")
    report["comparisons"] = []
    for record in report["records"]:
        name = {"noncurrent_borrowings": "LongtermBorrowings", "noncurrent_bonds": "BondsPayable"}.get(record["field"])
        if name is None or record["value"] is None:
            continue
        matches = [row["value"] for row in raw["records"] if row["type"] == name and row["date"] == record["period"]]
        matched = len(matches) == 1 and matches[0] == record["value"]
        check = {"field": record["field"], "period": record["period"],
                 "status": "matched" if matched else "needs_review", "official_value": record["value"],
                 "finmind_values": matches}
        report["comparisons"].append(check)
        if not matched:
            report["issues"].append(check)


def audit_batch(tickers: list[str], year: int, output: Path, *, refresh: bool = False, delay: float = 6) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    cached = processed = 0
    base = os.environ.get("DATA_SERVICE_URL", "http://localhost:8001").rstrip("/")
    # ponytail: 逐家公司執行並限速；需要提高吞吐量時再加來源允許的排程。
    with output.open("w", encoding="utf-8") as file:
        for index, ticker in enumerate(tickers):
            stop = False
            url = f"{base}/stocks/{ticker}/official-financials?" + urlencode({"year": year, "refresh": str(refresh).lower()})
            try:
                with urlopen(url, timeout=75) as response:
                    result = json.load(response)
                if (result.get("ticker") != ticker or result.get("filing_year") != year
                        or not isinstance(result.get("issues"), list) or result.get("can_screen") is not False):
                    raise ValueError
                if result.get("status") != "invalid_data":
                    params = urlencode({"dataset": "balance_sheet", "start_date": f"{year - 1}-12-31",
                                        "end_date": f"{year}-12-31"})
                    try:
                        with urlopen(f"{base}/stocks/{ticker}/fundamentals?{params}", timeout=40) as response:
                            compare_finmind(result, json.load(response))
                    except HTTPError as error:
                        result["issues"].append({"field": "finmind", "status": "source_error", "http_status": error.code})
                        stop = error.code in (429, 503)
                    except (OSError, ValueError, KeyError, TypeError, AttributeError):
                        result["issues"].append({"field": "finmind", "status": "source_error"})
            except HTTPError as error:
                status = "source_error"
                if error.code == 404:
                    try:
                        with error:
                            if json.load(error).get("detail") == "Not Found":
                                status = "service_outdated"
                    except (OSError, ValueError, AttributeError):
                        pass
                result = {"ticker": ticker, "filing_year": year, "status": status, "can_screen": False,
                          "issues": [{"field": "service", "status": status, "http_status": error.code}]}
                stop = error.code in (429, 503) or status == "service_outdated"
            except (OSError, ValueError, AttributeError):
                result = {"ticker": ticker, "filing_year": year, "status": "source_error", "can_screen": False,
                          "issues": [{"field": "service", "status": "source_error"}]}
            file.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
            file.flush()
            processed += 1
            cached += bool(result.get("cache_hit"))
            for issue in result["issues"]:
                key = (issue.get("field", "document"), issue["status"])
                if ticker not in groups[key]:
                    groups[key].append(ticker)
            if stop:
                break
            if index < len(tickers) - 1:
                time.sleep(delay)
    summary = {"year": year, "companies": processed, "cache_hits": cached, "remaining": tickers[processed:],
               "exceptions": [{"field": field, "status": status, "companies": codes}
                              for (field, status), codes in sorted(groups.items())]}
    output.with_suffix(".exceptions.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="*")
    parser.add_argument("--all", action="store_true", help="依本機股票清單批次查核；預設不掃全市場")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 2019 <= args.year < datetime.now(ZoneInfo("Asia/Taipei")).year:
        parser.error("年度必須為 2019 起已結束的西元年度")
    universe = {row["ticker"] for row in stock_universe()}
    if bool(args.tickers) == args.all or any(ticker not in universe for ticker in args.tickers):
        parser.error("請提供一般股票代號或--all，兩者擇一")
    tickers = sorted(universe) if args.all else list(dict.fromkeys(args.tickers))
    output = args.output or Path(f"data/processed/official-audit-{args.year}.jsonl")
    print(json.dumps(audit_batch(tickers, args.year, output, refresh=args.refresh), ensure_ascii=False))


if __name__ == "__main__":
    main()
