"""uv run python -m backend.api.check_fundamentals 2330 [income_statement]"""

import argparse
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from backend.data.universe import yahoo_symbol
from backend.screening.fundamental_quality import assess_fundamentals


def fetch_fundamental_data(ticker: str, dataset: str) -> dict:
    """共用中台 client；成功保留 raw，錯誤回明確狀態。"""
    try:
        yahoo_symbol(ticker)
        base = os.environ.get("DATA_SERVICE_URL", "http://localhost:8001").rstrip("/")
        url = f"{base}/stocks/{quote(ticker, safe='')}/fundamentals?dataset={quote(dataset, safe='')}"
        with urlopen(url, timeout=40) as response:
            raw = json.load(response)
        return raw
    except HTTPError as error:
        status, reason = "source_error", "中台無法提供這類基本面資料"
        if error.code == 404:
            try:
                with error:
                    detail = json.load(error).get("detail")
            except (OSError, ValueError, AttributeError):
                detail = None
            if detail == "Not Found":
                status = "service_outdated"
                reason = "中台沒有基本面路由，請確認 DATA_SERVICE_URL 並重啟本分支中台"
            elif detail == "指定股票與期間沒有這類基本面資料":
                status = "missing_data"
        return {"ticker": ticker, "status": status, "can_screen": False,
                "http_status": error.code, "reason": reason}
    except (OSError, ValueError):
        return {"ticker": ticker, "status": "source_error", "can_screen": False,
                "reason": "股票代碼無效，或中台連線／JSON 格式異常"}


def check_fundamentals(ticker: str, dataset: str = "income_statement") -> dict:
    raw = fetch_fundamental_data(ticker, dataset)
    return raw if isinstance(raw, dict) and "status" in raw else assess_fundamentals(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="基本面資料品質檢查，不是選股結果")
    parser.add_argument("ticker")
    parser.add_argument("dataset", nargs="?", default="income_statement",
                        choices=["income_statement", "balance_sheet", "cash_flow", "monthly_revenue", "dividends"])
    args = parser.parse_args()
    print(json.dumps(check_fundamentals(args.ticker, args.dataset), ensure_ascii=False, allow_nan=False))
