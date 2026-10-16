"""單股基本面計算及研究門檻；來源品質與條件符合度分開呈現。"""

import json
from datetime import date
from pathlib import Path

from backend.indicators.fundamental import (
    number,
    piotroski_score,
    previous_month,
    previous_quarter,
    revenue_yoy,
    roe_ttm,
)
from backend.screening.fundamental_quality import assess_fundamentals

# ponytail: 先核對驗收兩檔；依股票與年度精確匹配，其他股票／新年度保持缺資料。
_SUPPLEMENTS = json.loads(
    (Path(__file__).parents[1] / "data" / "fundamental_supplements.json").read_text(encoding="utf-8")
)


def evaluate_fundamental(data: dict, *, industry: str) -> dict:
    """輸入中台四張 raw 表。未驗證不宣稱已通過；缺少任何 F-score 訊號不湊總分。"""
    quality, tables = {}, {}
    if not isinstance(data, dict) or not isinstance(industry, str):
        return {"status": "invalid_data", "passed": None, "rules": [], "reason": "資料與產業格式不合法"}
    tickers = set()
    expected = {"income_statement": "TaiwanStockFinancialStatements",
                "balance_sheet": "TaiwanStockBalanceSheet",
                "cash_flow": "TaiwanStockCashFlowsStatement",
                "monthly_revenue": "TaiwanStockMonthRevenue"}
    try:
        for name, dataset in expected.items():
            raw = data.get(name)
            if isinstance(raw, dict) and "status" in raw:
                quality[name] = raw
                continue
            report = assess_fundamentals(raw)
            quality[name] = report
            if report["status"] in ("invalid_data", "missing_data"):
                continue
            if raw["dataset"] != dataset:
                raise ValueError("資料表類型與名稱不符")
            tickers.add(raw["ticker"])
            table = {}
            for row in raw["records"]:
                if name == "monthly_revenue":
                    key = (date(row["revenue_year"], row["revenue_month"], 1).isoformat(), "revenue")
                else:
                    previous_quarter(row["date"])  # 僅接受已明訂的曆年季末。
                    key = (row["date"], row["type"])
                if key in table:
                    raise ValueError(f"{name} 有重複期間／科目")
                table[key] = row.get("revenue" if name == "monthly_revenue" else "value")
            tables[name] = table
        if not tickers:
            failed = any(q.get("status") in ("source_error", "service_outdated", "missing_data") for q in quality.values())
            return {"status": "source_error" if failed else "invalid_data", "passed": None,
                    "rules": [], "quality": quality, "reason": "沒有可計算的來源資料"}
        if len(tickers) > 1:
            raise ValueError("資料缺少股票代碼或混入其他股票")
    except (TypeError, ValueError, KeyError) as error:
        return {"status": "invalid_data", "passed": None, "rules": [], "reason": str(error)}

    rules = []
    dependencies = set()

    def read(table, period, field):
        dependencies.add((table, period, field))
        if table not in tables or (period, field) not in tables[table]:
            raise ValueError(f"缺少 {table} {period} {field}")
        return number(tables[table][period, field])

    def latest(table):
        if table not in tables or not tables[table]:
            raise ValueError(f"缺少 {table}")
        return max(period for period, field in tables[table])

    def quarters(end):
        periods = [end]
        for _ in range(3):
            periods.append(previous_quarter(periods[-1]))
        return sorted(periods)

    def run(name, threshold, calculate):
        dependencies.clear()
        rule = {"id": name, "threshold": threshold, "value": None, "condition_met": None,
                "passed": None, "status": "insufficient_data", "reason": None}
        try:
            value, condition = calculate()
            rule.update(value=value, condition_met=condition,
                        status="calculated_unverified" if condition is not None else "insufficient_data")
            if condition is None:
                rule["reason"] = "必要資料不完整，不能判定門檻"
        except (ValueError, ArithmeticError) as error:
            rule["reason"] = str(error)
        relevant = []
        for table, period, field in sorted(dependencies):
            report = quality[table]
            status = report.get("status")
            if (status == "pending_update" and period == report.get("latest_period")) or status in (
                "source_error", "service_outdated", "invalid_data", "missing_data"
            ):
                relevant.append({"table": table, "status": report["status"]})
            for check in report.get("checks", []):
                if check["period"] == period and check["field"] == field and check["status"] != "matched":
                    relevant.append({"table": table, "status": "needs_review", "check": check})
        rule["inputs"] = [{"table": t, "period": p, "field": f} for t, p, f in sorted(dependencies)]
        if relevant:
            rule.update(status=relevant[0]["status"], condition_met=None,
                        reason="必要來源待更新、待核對或無法取得", quality_issues=relevant)
        rules.append(rule)

    def eps():
        periods = quarters(latest("income_statement"))
        values = [{"period": p, "eps": read("income_statement", p, "EPS")} for p in periods]
        return values, all(item["eps"] > 0 for item in values)

    def roe():
        end = latest("income_statement")
        periods = quarters(end)
        start = previous_quarter(periods[0])
        incomes = [read("income_statement", p, "IncomeAfterTaxes") for p in periods]
        opening = read("balance_sheet", start, "Equity")
        closing = read("balance_sheet", end, "Equity")
        value = roe_ttm(incomes, opening, closing)
        return {"percent": value, "periods": periods, "opening_period": start,
                "net_income": sum(incomes), "opening_equity": opening, "closing_equity": closing}, value > 12

    def revenue():
        end = latest("monthly_revenue")
        periods = [previous_month(previous_month(end)), previous_month(end), end]
        values = []
        for period in periods:
            day = date.fromisoformat(period)
            prior = date(day.year - 1, day.month, 1).isoformat()
            current_value, prior_value = read("monthly_revenue", period, "revenue"), read("monthly_revenue", prior, "revenue")
            values.append({"period": period, "revenue": current_value, "prior_year_revenue": prior_value,
                           "yoy_percent": revenue_yoy(current_value, prior_value)})
        return values, all(item["yoy_percent"] > 0 for item in values)

    def f_score():
        if any(word in industry for word in ("金融", "保險", "證券", "金控")):
            raise ValueError("此版 F-score 未適配金融業，不能套用一般產業科目")
        end = date.fromisoformat(latest("income_statement"))
        year = end.year if end.month == 12 else end.year - 1

        def optional(table, period, field):
            try:
                return read(table, period, field)
            except ValueError:
                return None

        def annual(year):
            period, opening = f"{year}-12-31", f"{year - 1}-12-31"
            result = {"year": year, "equity_issued": None}
            for key, table, field, at in [
                ("assets", "balance_sheet", "TotalAssets", period),
                ("opening_assets", "balance_sheet", "TotalAssets", opening),
                ("current_assets", "balance_sheet", "CurrentAssets", period),
                ("current_liabilities", "balance_sheet", "CurrentLiabilities", period),
                ("operating_cash_flow", "cash_flow", "CashFlowsFromOperatingActivities", period),
            ]:
                result[key] = optional(table, at, field)
            for key, field in [("net_income", "IncomeAfterTaxes"), ("revenue", "Revenue"), ("gross_profit", "GrossProfit")]:
                values = [optional("income_statement", p, field) for p in quarters(period)]
                result[key] = sum(values) if all(v is not None for v in values) else None
            result["long_term_debt"] = None
            supplements = [item for item in _SUPPLEMENTS["records"]
                           if item["ticker"] == next(iter(tickers)) and item["year"] == year]
            if len(supplements) == 1:
                supplement = supplements[0]
                components = [number(supplement[key]) for key in
                              ("noncurrent_bonds", "noncurrent_borrowings", "noncurrent_leases")]
                if any(value < 0 for value in components):
                    raise ValueError("人工核對長債金額不可為負數")
                result["long_term_debt"] = number(sum(components))
                issued = supplement.get("equity_issued")
                result["equity_issued"] = issued if type(issued) is bool else None
                result["supplement"] = {**supplement, "reviewed_on": _SUPPLEMENTS["reviewed_on"],
                                        "basis": _SUPPLEMENTS["basis"], "method": "manual_company_filing"}
            return result

        current, previous = annual(year), annual(year - 1)
        result = piotroski_score(current, previous)
        result.update(year=year, inputs={"current": current, "previous": previous},
                      limitations=["長債與普通股發行只在人工核對股票／年度提供；並非全市場自動抓取或完整來源驗證"])
        return result, result["score"] >= 6 if result["score"] is not None else None

    run("eps_positive_four_quarters", "四個連續季度 EPS 均 > 0", eps)
    run("roe_ttm", "近四季 ROE > 12%（合併淨利／期初期末平均合併權益）", roe)
    run("revenue_yoy_three_months", "三個連續月營收 YoY 均 > 0%", revenue)
    run("piotroski_f_score", "年度 F-score >= 6／9", f_score)
    conditions = [rule["condition_met"] for rule in rules]
    monthly = []
    if tables.get("monthly_revenue"):
        end = latest("monthly_revenue")
        periods = [end]
        for _ in range(5):
            periods.append(previous_month(periods[-1]))
        for period in sorted(periods):
            current_value = tables["monthly_revenue"].get((period, "revenue"))
            day = date.fromisoformat(period)
            prior = date(day.year - 1, day.month, 1).isoformat()
            prior_value = tables["monthly_revenue"].get((prior, "revenue"))
            try:
                yoy = revenue_yoy(current_value, prior_value)
            except ValueError:
                yoy = None
            monthly.append({"month": period[:7], "revenue": current_value, "yoy": yoy})
    return {"ticker": next(iter(tickers)), "rule_version": "fundamental-v1-research",
            "scope": "fundamental_only", "status": "incomplete" if None in conditions else "calculated_unverified",
            "passed": None, "conditions_met": all(conditions) if None not in conditions else None,
            "rules": rules, "quality": quality, "monthly_revenue": monthly,
            "reason": "研究計算未全面驗證；未知條件不等於合格或不合格，並非歷史回測可知資料"}
