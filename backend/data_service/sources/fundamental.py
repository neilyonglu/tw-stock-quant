"""FinMind 原始財報、月營收與股利；不計算財務比率或篩選分數。"""

import json
import os
from datetime import UTC, date, datetime
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from backend.data_service.cache import ttl_cache

Dataset = Literal["income_statement", "balance_sheet", "cash_flow", "monthly_revenue", "dividends"]
DATASETS = {
    "income_statement": "TaiwanStockFinancialStatements",
    "balance_sheet": "TaiwanStockBalanceSheet",
    "cash_flow": "TaiwanStockCashFlowsStatement",
    "monthly_revenue": "TaiwanStockMonthRevenue",
    "dividends": "TaiwanStockDividend",
}


@ttl_cache(seconds=1800)
def fetch_fundamentals(ticker: str, dataset: Dataset, start_date: date, end_date: date) -> dict:
    params = urlencode({"dataset": DATASETS[dataset], "data_id": ticker,
                        "start_date": start_date.isoformat(), "end_date": end_date.isoformat()})
    headers = {"User-Agent": "tw-stock-quant"}
    if token := os.environ.get("FINMIND_TOKEN", "").strip():
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.finmindtrade.com/api/v4/data?{params}", headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as error:
        status = 503 if error.code == 429 else 502
        raise HTTPException(status, "FinMind 暫時無法提供資料（限額、授權或上游錯誤）") from None
    except TimeoutError:
        raise HTTPException(504, "FinMind 請求逾時") from None
    except URLError:
        raise HTTPException(502, "無法連線至 FinMind") from None
    except OSError:
        raise HTTPException(502, "FinMind 連線中斷") from None
    except (ValueError, UnicodeError):
        raise HTTPException(502, "FinMind 回傳無效 JSON") from None

    if not isinstance(payload, dict):
        raise HTTPException(502, "FinMind 回傳格式異常")
    if payload.get("status") != 200:
        status = 503 if payload.get("status") == 429 else 502
        # 不轉傳上游訊息，避免憑證或內部網址隨錯誤流出。
        raise HTTPException(status, "FinMind 暫時無法提供資料（限額、授權或上游錯誤）")
    rows = payload.get("data")
    try:
        if not isinstance(rows, list):
            raise ValueError
        for row in rows:
            if row["stock_id"] != ticker:
                raise ValueError
            period = date.fromisoformat(row["date"])
            if not start_date <= period <= end_date:
                raise ValueError
            if dataset in ("income_statement", "balance_sheet", "cash_flow"):
                if not isinstance(row["type"], str) or not row["type"]:
                    raise ValueError
                value = row["value"]
                if value is not None and type(value) not in (int, float):
                    raise ValueError
            elif dataset == "monthly_revenue":
                revenue_period = date(row["revenue_year"], row["revenue_month"], 1)
                if revenue_period > period:
                    raise ValueError
                value = row["revenue"]
                if value is not None and type(value) not in (int, float):
                    raise ValueError
        json.dumps(rows, allow_nan=False)
    except (KeyError, TypeError, ValueError, OverflowError):
        raise HTTPException(502, "FinMind 資料欄位或數值異常") from None
    if not rows:
        raise HTTPException(404, "指定股票與期間沒有這類基本面資料")
    return {
        "ticker": ticker,
        "source": "FinMind",
        "dataset": DATASETS[dataset],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "fetched_at": datetime.now(UTC).isoformat(),
        "records": sorted(rows, key=lambda row: row["date"]),
    }
