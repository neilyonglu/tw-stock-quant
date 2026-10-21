"""資料中台：唯一負責向外部來源（yfinance/twstock/FinMind）抓取＋快取資料的服務。

前端（顯示）和後端（計算，隊友另開 branch 開發）都跟這個服務要資料，不各自
重新打外部 API——避免 API 延遲，也避免抓取邏輯重複造輪子。詳見
PROJECT.md「架構：中台 / 前端 / 後端」。

本機啟動：uv run uvicorn backend.data_service.main:app --reload --port 8001
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException

from backend.data.universe import yahoo_symbol
from backend.data_service.sources import fundamental, intraday, market, official, stock

app = FastAPI(title="tw-stock-quant data service")


def _stock_symbol(ticker: str) -> str:
    try:
        return yahoo_symbol(ticker)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stocks/search")
def search_stocks(q: str = ""):
    return stock.search_stocks(q)


@app.get("/stocks/{ticker}/candles")
def get_candles(ticker: str, period: str = "6mo", interval: str = "1d"):
    _stock_symbol(ticker)
    data = stock.fetch_candles(ticker, period, interval)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@app.get("/stocks/{ticker}/profile")
def get_profile(ticker: str):
    _stock_symbol(ticker)
    return stock.fetch_profile(ticker)


@app.get("/stocks/{ticker}/fundamentals")
def get_fundamentals(
    ticker: str,
    dataset: fundamental.Dataset,
    start_date: date | None = None,
    end_date: date | None = None,
):
    _stock_symbol(ticker)
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    start_date = start_date or date(today.year - 4, 1, 1)
    end_date = end_date or today
    if not start_date <= end_date <= today:
        raise HTTPException(422, "日期須符合 start_date ≤ end_date ≤ 台北今日")
    return fundamental.fetch_fundamentals(ticker, dataset, start_date, end_date)


@app.get("/stocks/{ticker}/official-financials")
def get_official_financials(ticker: str, year: int, refresh: bool = False):
    _stock_symbol(ticker)
    if not 2019 <= year < datetime.now(ZoneInfo("Asia/Taipei")).year:
        raise HTTPException(422, "年度必須為 2019 起已結束的西元年度")
    return official.fetch_official_financials(ticker, year, refresh)


@app.get("/stocks/{ticker}/orderbook")
def get_orderbook(ticker: str):
    _stock_symbol(ticker)
    data = stock.fetch_orderbook(ticker)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@app.get("/stocks/{ticker}/intraday")
def get_stock_intraday(ticker: str):
    data = intraday.fetch_intraday(_stock_symbol(ticker))
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@app.get("/market/indices")
def get_market_indices():
    return market.fetch_market_indices()


@app.get("/market/intraday")
def get_market_intraday():
    data = intraday.fetch_intraday("^TWII")
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data
