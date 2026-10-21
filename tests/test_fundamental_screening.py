import copy
import io
import json

import pytest

from backend.api import check_fundamentals, screen_fundamental
from backend.indicators.fundamental import piotroski_score, revenue_yoy, roe_ttm
from backend.screening.fundamental import evaluate_fundamental


def sample():
    datasets = {"income_statement": "TaiwanStockFinancialStatements",
                "balance_sheet": "TaiwanStockBalanceSheet", "cash_flow": "TaiwanStockCashFlowsStatement",
                "monthly_revenue": "TaiwanStockMonthRevenue"}
    data = {key: {"ticker": "2317", "source": "FinMind", "dataset": dataset,
                  "fetched_at": "2026-10-16T00:00:00+00:00", "start_date": "2022-01-01",
                  "end_date": "2026-10-16", "records": []} for key, dataset in datasets.items()}
    for year in range(2022, 2027):
        for suffix in ["03-31", "06-30", "09-30", "12-31"]:
            period = f"{year}-{suffix}"
            if period > "2026-06-30":
                continue
            for field, value in [("EPS", 1), ("IncomeAfterTaxes", 40), ("Revenue", 200), ("GrossProfit", 80)]:
                data["income_statement"]["records"].append({"stock_id": "2317", "date": period, "type": field, "value": value})
            for field, value in [("Equity", 1000), ("TotalAssets", 2000), ("CurrentAssets", 700), ("CurrentLiabilities", 300)]:
                data["balance_sheet"]["records"].append({"stock_id": "2317", "date": period, "type": field, "value": value})
            data["cash_flow"]["records"].append({"stock_id": "2317", "date": period,
                                                  "type": "CashFlowsFromOperatingActivities", "value": 240})
    for year, revenue in [(2025, 100), (2026, 120)]:
        for month in [7, 8, 9]:
            data["monthly_revenue"]["records"].append({"stock_id": "2317", "date": f"{year}-{month+1:02d}-01",
                "revenue_year": year, "revenue_month": month, "revenue": revenue})
    return data


def test_basic_metrics_periods_thresholds_and_missing_f_score_stay_honest():
    data = sample()
    original = copy.deepcopy(data)
    result = evaluate_fundamental(data, industry="其他電子業")
    assert data == original and result["passed"] is None
    eps, roe, revenue, fscore = result["rules"]
    assert eps["condition_met"] is True
    assert [r["period"] for r in eps["value"]] == ["2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]
    assert roe["value"]["percent"] == 16 and roe["value"]["opening_period"] == "2025-06-30"
    assert revenue["condition_met"] is True and revenue["value"][-1]["period"] == "2026-09-01"
    assert revenue["value"][-1]["yoy_percent"] == pytest.approx(20)
    assert fscore["value"]["year"] == 2025 and fscore["value"]["score"] is None
    assert fscore["value"]["known_signals"] == 7
    assert fscore["status"] == "insufficient_data" and result["conditions_met"] is None


def test_zero_negative_and_missing_quarters_are_not_silently_skipped():
    data = sample()
    row = next(r for r in data["income_statement"]["records"] if r["date"] == "2026-06-30" and r["type"] == "EPS")
    row["value"] = 0
    assert evaluate_fundamental(data, industry="電子業")["rules"][0]["condition_met"] is False
    data["income_statement"]["records"].remove(row)
    assert evaluate_fundamental(data, industry="電子業")["rules"][0]["status"] == "insufficient_data"
    row = data["monthly_revenue"]["records"][-1]
    row["revenue"] = 0
    result = evaluate_fundamental(data, industry="電子業")["rules"][2]
    assert result["value"][-1]["yoy_percent"] == -100 and result["condition_met"] is False


def test_gaps_mixed_stocks_and_financial_sector_are_explicit():
    data = sample()
    data["monthly_revenue"]["records"].pop(-2)
    assert evaluate_fundamental(data, industry="金融業")["rules"][2]["status"] == "insufficient_data"
    assert "未適配金融業" in evaluate_fundamental(data, industry="金融業")["rules"][3]["reason"]
    data["cash_flow"]["ticker"] = "2330"
    data["cash_flow"]["records"] = [{**r, "stock_id": "2330"} for r in data["cash_flow"]["records"]]
    assert evaluate_fundamental(data, industry="電子業")["status"] == "invalid_data"


def test_f_score_nine_signals_and_unknown_is_not_a_zero_or_a_complete_score():
    previous = {"net_income": 5, "operating_cash_flow": 10, "opening_assets": 100, "assets": 100,
                "long_term_debt": 40, "current_assets": 20, "current_liabilities": 20,
                "revenue": 50, "gross_profit": 10}
    current = {"net_income": 20, "operating_cash_flow": 30, "opening_assets": 100, "assets": 120,
               "long_term_debt": 20, "current_assets": 40, "current_liabilities": 20,
               "revenue": 100, "gross_profit": 40, "equity_issued": False}
    assert piotroski_score(current, previous)["score"] == 9
    current["equity_issued"] = True
    assert piotroski_score(current, previous)["score"] == 8
    current["equity_issued"] = None
    assert piotroski_score(current, previous)["score"] is None
    current["equity_issued"] = False
    current["long_term_debt"] = 44  # 與前一年槓桿相同，非改善，不加分。
    assert piotroski_score(current, previous)["score"] == 8
    current["operating_cash_flow"] = 20  # 與淨利相等，非較高。
    assert piotroski_score(current, previous)["score"] == 7


@pytest.mark.parametrize("denominator", [0, -1, None, float("nan"), float("inf"), True])
def test_financial_denominators_are_validated(denominator):
    with pytest.raises(ValueError):
        revenue_yoy(100, denominator)
    with pytest.raises(ValueError):
        roe_ttm([1, 2, 3, 4], denominator, 100)


def test_cli_reuses_raw_client_and_requests_only_needed_datasets(monkeypatch):
    data = sample()
    for raw in data.values():
        raw["ticker"] = "6488"
        for row in raw["records"]:
            row["stock_id"] = "6488"
    calls = []

    def source(url, timeout):
        dataset = url.split("dataset=")[1]
        calls.append(dataset)
        return io.BytesIO(json.dumps(data[dataset]).encode())

    monkeypatch.setattr(check_fundamentals, "urlopen", source)
    result = screen_fundamental.screen_fundamental("6488")
    assert len(calls) == 4 and result["passed"] is None
    assert screen_fundamental.screen_fundamental("not-stock")["status"] == "invalid_data"


def test_announcement_blocks_latest_quarter_but_not_prior_completed_annual_period():
    data = sample()
    for raw in data.values():
        raw["ticker"] = "2330"
        for row in raw["records"]:
            row["stock_id"] = "2330"
    result = evaluate_fundamental(data, industry="半導體業")
    assert result["rules"][0]["status"] == "pending_update"
    assert result["rules"][1]["status"] == "pending_update"
    assert result["rules"][3]["status"] == "calculated_unverified"
    assert result["rules"][3]["value"]["known_signals"] == 9
    assert result["rules"][3]["value"]["year"] == 2025


def test_source_failures_are_preserved_and_official_eps_reconciliation_matches():
    errors = {name: {"status": "source_error", "can_screen": False} for name in sample()}
    assert evaluate_fundamental(errors, industry="電子業")["status"] == "source_error"
    assert evaluate_fundamental(None, industry="電子業")["status"] == "invalid_data"
    # 正式年度／前三季累計 EPS 對照已修正，原始 4.61 不再錯誤阻擋。
    from backend.screening.fundamental_quality import assess_fundamentals
    data = sample()["income_statement"]
    data["ticker"] = "6488"
    for row in data["records"]:
        row["stock_id"] = "6488"
        if row["type"] == "EPS" and row["date"] == "2025-12-31":
            row["value"] = 4.61
    result = assess_fundamentals(data)
    check = next(c for c in result["checks"] if c["period"] == "2025-12-31")
    assert check["status"] == "matched"


def test_supplements_match_only_reviewed_company_year_and_revenue_has_six_calendar_months():
    data = sample()
    for raw in data.values():
        raw["ticker"] = "6488"
        for row in raw["records"]:
            row["stock_id"] = "6488"
    result = evaluate_fundamental(data, industry="半導體業")
    score = result["rules"][3]["value"]
    assert score["known_signals"] == 9 and score["score"] is not None
    annual = score["inputs"]["current"]
    assert annual["long_term_debt"] == (35679196 + 7564868 + 649360) * 1000
    assert annual["equity_issued"] is False
    assert annual["supplement"]["method"] == "manual_company_filing"
    assert annual["supplement"]["reviewed_on"] == "2026-10-16"
    monthly = result["monthly_revenue"]
    assert [row["month"] for row in monthly] == [f"2026-{m:02d}" for m in range(4, 10)]
    assert monthly[0]["revenue"] is None and monthly[-1]["revenue"] == 120
    assert monthly[-1]["yoy"] == pytest.approx(20)
    # 新年度不可沿用舊年度補充值。
    for field, value in [("EPS", 1), ("IncomeAfterTaxes", 40), ("Revenue", 200), ("GrossProfit", 80)]:
        data["income_statement"]["records"].append({"stock_id": "6488", "date": "2026-12-31", "type": field, "value": value})
    for raw in data.values():
        raw["end_date"] = "2026-12-31"
    current = evaluate_fundamental(data, industry="半導體業")["rules"][3]["value"]["inputs"]["current"]
    assert current["year"] == 2026 and current["long_term_debt"] is None and current["equity_issued"] is None
    assert "supplement" not in current


@pytest.mark.parametrize("ticker,current_debt,previous_debt", [
    ("2409", 83_830_295_000, 110_677_329_000),
    ("3481", 20_814_419_000, 23_467_459_000),
])
def test_reviewed_panel_filings_complete_signals_only_for_reviewed_years(ticker, current_debt, previous_debt):
    data = sample()
    for raw in data.values():
        raw["ticker"] = ticker
        for row in raw["records"]:
            row["stock_id"] = ticker
    result = evaluate_fundamental(data, industry="光電業")
    score = result["rules"][3]["value"]
    assert score["year"] == 2025 and score["known_signals"] == 9
    assert score["score"] is not None and result["passed"] is None
    assert score["inputs"]["current"]["long_term_debt"] == current_debt
    assert score["inputs"]["previous"]["long_term_debt"] == previous_debt
    assert score["inputs"]["current"]["equity_issued"] is False
    assert score["inputs"]["current"]["supplement"]["reviewed_on"] == "2026-10-21"
    assert score["inputs"]["current"]["supplement"]["noncurrent_bonds"] == 0
    for field, value in [("EPS", 1), ("IncomeAfterTaxes", 40), ("Revenue", 200), ("GrossProfit", 80)]:
        data["income_statement"]["records"].append({"stock_id": ticker, "date": "2026-12-31", "type": field, "value": value})
    for raw in data.values():
        raw["end_date"] = "2026-12-31"
    score = evaluate_fundamental(data, industry="光電業")["rules"][3]["value"]
    assert score["year"] == 2026 and score["score"] is None
    assert "supplement" not in score["inputs"]["current"]


@pytest.mark.parametrize("table", ["income_statement", "balance_sheet", "cash_flow"])
def test_duplicate_financial_pairs_remain_invalid_without_failing_stock(table):
    data = sample()
    data[table]["records"].append({**data[table]["records"][0], "value": -999})
    result = evaluate_fundamental(data, industry="電子業")
    assert result["status"] == "invalid_data" and result["passed"] is None
    assert result["rules"] == []


def test_future_revenue_year_cannot_create_passing_growth_rule():
    data = sample()
    for row in data["monthly_revenue"]["records"]:
        row["revenue_year"] += 73
    result = evaluate_fundamental(data, industry="電子業")
    assert result["passed"] is None and result["conditions_met"] is None
    assert result["quality"]["monthly_revenue"]["status"] == "invalid_data"
    revenue = result["rules"][2]
    assert revenue["condition_met"] is None and revenue["value"] is None
    assert result["monthly_revenue"] == []
