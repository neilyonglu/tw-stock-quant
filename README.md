# tw-stock-quant

[繁體中文](README.zh-TW.md) | English

A personal quantitative analysis system for the Taiwan stock market (TWSE/TPEX). Covers the full pipeline from data ingestion and technical indicators to multi-factor stock screening, portfolio optimization, automated scheduling, and Telegram notifications — fully self-built, no black-box subscriptions.

> **Disclaimer**: For personal learning and research only. Not investment advice.

---

## Features

- **Technical Analysis**: TA-Lib (150+ indicators, 61 candlestick patterns)
- **Strategy Backtesting**: `backtesting.py` with Sharpe ratio, max drawdown, win-rate reporting
- **Fundamental Screening**: Piotroski F-score, FCF conversion, monthly revenue YoY
- **Chip / Institutional Flow**: Foreign investors, investment trusts, proprietary traders, margin data (FinMind)
- **Multi-Factor Scoring**: Macro → fundamental → chip → technical
- **Portfolio Optimization**: `pyportfolioopt` (mean-variance, risk parity)
- **Automated Scheduling**: Runs every Friday after market close
- **Push Notifications**: Telegram Bot

---

## Installation

```bash
git clone https://github.com/neilyonglu/tw-stock-quant.git
cd tw-stock-quant
uv sync
```

Copy `.env.example` to `.env` and fill in any API keys (all optional — system falls back to free alternatives).

---

## Dashboard

A web-based analysis dashboard built with **Next.js 16 + Tailwind v4 + shadcn/ui + TradingView lightweight-charts**, served alongside a Python data layer.

| Step | Page | Status |
|------|------|--------|
| 0 | Project scaffold (Next.js + shadcn + lightweight-charts) | ✅ Done |
| 1 | App shell (sidebar + 3-page routing) | ✅ Done |
| 2 | Stock analysis page — 5-pane K-line chart, 7 timeframes, intraday/fundamentals/chip/order-book/news tabs (real data where yfinance/twstock allow, mocked elsewhere) | ✅ Done |
| 3 | Market overview page — indices (real), institutional flows/breadth/rankings/futures/news (mocked pending Phase 1/4/5/6 backend) | ✅ Done |
| 4 | Weekly screening results page (mock data) | Pending |

See [docs/thinking.md](docs/thinking.md) for the full real-vs-mock data inventory per field.

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment setup | ✅ Done |
| 1 | Data pipeline (twstock → Parquet) | Pending |
| 2 | Technical indicators (TA-Lib) | Pending |
| 3 | Strategy backtesting (backtesting.py) | Pending |
| 4 | Fundamental integration (CasualMarket) | Pending |
| 5 | Chip data + macro context (FinMind) | Pending |
| 6 | Stock screener + portfolio optimizer + scheduling | Pending |
| 7 | Factor validation + event study | Pending |
| 8 | Sentiment (Google Trends / pytrends) | Pending |
| 9 | Dashboard API (FastAPI migration) | Pending |

---

## Data Sources

| Tool | Purpose |
|------|---------|
| [twstock](https://github.com/mlouielu/twstock) | Historical OHLCV, real-time quotes |
| [FinMind](https://finmind.github.io/) | Institutional flow, margin data, financial statements |
| [CasualMarket](https://github.com/sacahan/CasualMarket) | Financials, monthly revenue, dividends (MCP Server) |
| TWSE OpenAPI | Market breadth, official price data |
| yfinance | USD/TWD exchange rate, US treasury yield |
| data.gov.tw | Taiwan business cycle indicators |

---

## References

- [locupleto/streamlit-lightweight-charts-v5](https://github.com/locupleto/streamlit-lightweight-charts-v5) (MIT)
- [kevin801221/stock-strategies-only](https://github.com/kevin801221/stock-strategies-only) (MIT)

---

## License

[MIT](LICENSE)
