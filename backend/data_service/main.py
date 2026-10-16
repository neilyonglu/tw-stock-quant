"""資料中台：唯一負責向外部來源（yfinance/twstock）抓取＋快取資料的服務。

前端（顯示）和後端（計算，隊友另開 branch 開發）都跟這個服務要資料，不各自
重新打外部 API——避免 API 延遲，也避免抓取邏輯重複造輪子。詳見
PROJECT.md「架構：中台 / 前端 / 後端」。

本機啟動：uv run uvicorn backend.data_service.main:app --reload --port 8001
"""
from fastapi import FastAPI, HTTPException

from backend.data.universe import yahoo_symbol
from backend.data_service.sources import intraday, market, stock

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
