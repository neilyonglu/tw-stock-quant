"""原始基本面資料的品質報告；不改來源值、不計算投資分數。"""

import json
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from backend.data_service.sources.announcements import DATASETS, SOURCES, valid_source

_REFERENCES = json.loads(
    (Path(__file__).parents[1] / "data" / "fundamental_references.json").read_text(encoding="utf-8")
)
PERIOD_BASIS = {
    "TaiwanStockFinancialStatements": "quarterly",
    "TaiwanStockBalanceSheet": "point_in_time",
    "TaiwanStockCashFlowsStatement": "year_to_date",
    "TaiwanStockMonthRevenue": "monthly",
    "TaiwanStockDividend": "distribution_record",
}


def assess_fundamentals(raw: dict) -> dict:
    """只回品質摘要；尚無全面驗證時 can_screen 為 None，已知問題為 False。

    公告追蹤由中台提供；人工公告與科目比對仍保留。
    """
    report = {"status": "invalid_data", "can_screen": False, "latest_period": None,
              "freshness": "unknown", "period_basis": None, "checks": [], "issues": []}
    try:
        ticker, dataset = raw["ticker"], raw["dataset"]
        if raw["source"] != "FinMind" or dataset not in PERIOD_BASIS:
            raise ValueError("不支援的來源或資料表")
        if not isinstance(ticker, str) or not ticker:
            raise ValueError("缺少股票代碼")
        datetime.fromisoformat(raw["fetched_at"])
        start, end = date.fromisoformat(raw["start_date"]), date.fromisoformat(raw["end_date"])
        if start > end:
            raise ValueError("查詢起日大於迄日")
        report.update(ticker=ticker, dataset=dataset, source=raw["source"],
                      fetched_at=raw["fetched_at"], references_reviewed_on=_REFERENCES["reviewed_on"])
        tracking = raw.get("announcement_tracking", {
            "status": "unavailable" if ticker in SOURCES and dataset in DATASETS else "unsupported",
            "records": [], "can_screen": False,
            "reason": "Automatic announcement metadata not supplied; manual references still apply",
        })
        if (not isinstance(tracking, dict)
                or tracking.get("status") not in ("available", "unavailable", "unsupported", "source_error")
                or not isinstance(tracking.get("records"), list)):
            raise ValueError("公告追蹤格式不合法")
        expected_kind = {"TaiwanStockFinancialStatements": "earnings_release",
                         "TaiwanStockMonthRevenue": "monthly_revenue_announcement"}.get(dataset)
        if tracking["records"] and (
                ticker not in SOURCES or tracking.get("ticker") != ticker
                or tracking.get("dataset") != dataset or tracking.get("source") != SOURCES[ticker][0]
                or tracking.get("source_url") != SOURCES[ticker][1]
                or tracking["status"] not in ("available", "source_error")):
            raise ValueError("公告追蹤來源或股票不符")
        for item in tracking["records"]:
            if (not isinstance(item, dict) or expected_kind is None
                    or item.get("ticker") != ticker or item.get("dataset") != dataset
                    or item.get("source_kind") != expected_kind
                    or not valid_source(ticker, item)):
                raise ValueError("公告股票、資料表或來源不符")
            datetime.fromisoformat(item["fetched_at"])
            if date.fromisoformat(item["period"]) >= date.fromisoformat(item["published_on"]):
                raise ValueError("公告日必須晚於報告期間")
        report["announcement_tracking"] = tracking
        report["period_basis"] = PERIOD_BASIS[dataset]
        rows = raw["records"]
        if not isinstance(rows, list):
            raise ValueError("records 必須是陣列")
        if not rows:
            report.update(status="missing_data", issues=["沒有資料"])
            return report
        periods = []
        seen = set()
        for row in rows:
            if row["stock_id"] != ticker:
                raise ValueError("資料混入其他股票")
            period = date.fromisoformat(row["date"])
            if not start <= period <= end:
                raise ValueError("來源日期超出查詢範圍")
            if dataset == "TaiwanStockMonthRevenue":
                revenue_period = date(row["revenue_year"], row["revenue_month"], 1)
                if revenue_period > period:
                    raise ValueError("月營收所屬月份晚於來源日期")
                period = revenue_period
            if dataset in ("TaiwanStockFinancialStatements", "TaiwanStockBalanceSheet",
                           "TaiwanStockCashFlowsStatement"):
                if not isinstance(row["type"], str) or not row["type"]:
                    raise ValueError("缺少財報科目")
                key = (period, row["type"])
                if key in seen:
                    report["issues"].append(f"{row['date']} {row['type']}: ambiguous_data")
                seen.add(key)
                value = row["value"]
                if value is not None and (type(value) not in (int, float)
                                          or not Decimal(str(value)).is_finite()):
                    raise ValueError("財報含無效數值")
            elif dataset == "TaiwanStockMonthRevenue":
                value = row["revenue"]
                if value is not None and (type(value) not in (int, float)
                                          or not Decimal(str(value)).is_finite()):
                    raise ValueError("月營收含無效數值")
                if period in seen:
                    raise ValueError("月營收所屬月份重複")
                seen.add(period)
            periods.append(period.isoformat())
        report["latest_period"] = max(periods)
        report.update(status="needs_review" if report["issues"] else "unverified",
                      can_screen=False if report["issues"] else None)

        announcements = [item for item in _REFERENCES["announcements"]
                         if item["ticker"] == ticker and item["dataset"] == dataset
                         and date.fromisoformat(item["published_on"]) <= end]
        manual = announcements.copy()
        if manual:
            report["reviewed_announcement"] = max(manual, key=lambda item: item["period"])
        if tracking.get("status") in ("available", "source_error"):
            announcements += [item for item in tracking["records"]
                              if date.fromisoformat(item["published_on"]) <= end]
        if tracking.get("status") == "source_error":
            report["can_screen"] = False
        if announcements:
            latest = max(announcements, key=lambda item: item["period"])
            report["latest_announcement"] = latest
            if report["latest_period"] < latest["period"]:
                report.update(freshness="pending_update", status="pending_update", can_screen=False)
                source_kind = latest.get("source_kind")
                if source_kind == "earnings_release":
                    message = (f"{latest['period']} 業績摘要已公布；FinMind 財報資料目前僅到 "
                               f"{report['latest_period']}。業績摘要不代表完整核閱財報。")
                elif source_kind == "reviewed_financial_statement":
                    message = (f"{latest['period']} 完整核閱財報已公布；FinMind 財報資料目前僅到 "
                               f"{report['latest_period']}。")
                elif source_kind == "monthly_revenue_announcement":
                    message = (f"{latest['period'][:7]} 月營收已公布；FinMind 月營收目前僅到 "
                               f"{report['latest_period'][:7]}。")
                else:
                    message = "來源期間落後已人工確認的公司公告"
                report["issues"].append(message)
            else:
                report["freshness"] = ("at_least_reviewed_period" if latest in manual
                                       else "at_least_announced_period")

        for reference in _REFERENCES["comparisons"]:
            if reference["ticker"] != ticker or reference["dataset"] != dataset:
                continue
            matches = [row for row in rows if row.get("type") == reference["field"]
                       and row["date"] == reference["period"]]
            # 使用者查較短期間時，區間外的歷史差異不影響這次報告。
            if not start <= date.fromisoformat(reference["period"]) <= end:
                continue
            check = {**reference, "observed_value": None, "status": "missing_data"}
            if len(matches) > 1:
                check["status"] = "ambiguous_data"
            elif matches and matches[0].get("value") is not None:
                value = matches[0]["value"]
                if type(value) not in (int, float) or not Decimal(str(value)).is_finite():
                    raise ValueError("比對科目含無效數值")
                check["observed_value"] = value
                precision = Decimal(reference["precision"])
                rounded = (Decimal(str(value)) / precision).to_integral_value(rounding=ROUND_HALF_UP)
                expected = Decimal(reference["reference_value"]) / precision
                check["status"] = "matched" if rounded == expected else "needs_review"
            report["checks"].append(check)
            if check["status"] != "matched":
                report["can_screen"] = False
                report["issues"].append(f"{reference['period']} {reference['field']}: {check['status']}")
                if report["status"] != "pending_update":
                    report["status"] = "needs_review"
        return report
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        report.update(status="invalid_data", can_screen=False, issues=[str(error)])
        return report
