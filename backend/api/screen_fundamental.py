"""uv run python -m backend.api.screen_fundamental 2330"""

import argparse
import json

import twstock

from backend.api.check_fundamentals import fetch_fundamental_data
from backend.data.universe import yahoo_symbol
from backend.screening.fundamental import evaluate_fundamental


def screen_fundamental(ticker: str) -> dict:
    try:
        yahoo_symbol(ticker)
    except ValueError as error:
        return {"ticker": ticker, "status": "invalid_data", "passed": None, "reason": str(error)}
    raw = {name: fetch_fundamental_data(ticker, name)
           for name in ("income_statement", "balance_sheet", "cash_flow", "monthly_revenue")}
    return evaluate_fundamental(raw, industry=twstock.codes[ticker].group)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="基本面研究計算及品質限制")
    parser.add_argument("ticker")
    print(json.dumps(screen_fundamental(parser.parse_args().ticker), ensure_ascii=False, allow_nan=False))
