# tw-stock-quant

A personal quantitative analysis system for the Taiwan stock market (TWSE/TPEX). Covers the full pipeline from data ingestion and technical indicators to multi-factor stock screening, portfolio optimization, automated scheduling, and Telegram notifications — fully self-built, no black-box subscriptions.

> **Disclaimer**: This project is for personal learning and research only. Nothing here constitutes investment advice.

---

## Features

- **Live Dashboard**: Streamlit + TradingView-grade candlestick charts via `streamlit-lightweight-charts-v5`
- **Technical Analysis**: TA-Lib (150+ indicators, 61 candlestick pattern recognizers)
- **Strategy Backtesting**: `backtesting.py` with Sharpe ratio, max drawdown, and win-rate reporting
- **Fundamental Screening**: Piotroski F-score, FCF conversion rate, monthly revenue YoY
- **Chip / Institutional Flow**: Foreign investors, investment trusts, proprietary traders, margin data (FinMind)
- **Multi-Factor Scoring**: Four-layer framework — macro → fundamental → chip → technical
- **Portfolio Optimization**: `pyportfolioopt` (mean-variance, risk parity)
- **Automated Scheduling**: GitHub Actions — runs every Friday after market close, no server required
- **Push Notifications**: Telegram Bot

---

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/neilyonglu/tw-stock-quant.git
cd tw-stock-quant
uv sync
```

### Environment Variables (all optional)

```bash
cp .env.example .env
# Fill in any API keys you want to use
```

See [.env.example](.env.example) for details. Every key is optional — the system falls back to free alternatives.

---

## Running the Dashboard

```bash
streamlit run src/dashboard/app.py
```

Open `http://localhost:8501` in your browser.

---

## Roadmap

Full details in [plan.md](plan.md).

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment setup | ✅ Done |
| 1 | Data pipeline (twstock → Parquet) | In progress |
| 2 | Technical indicators (TA-Lib) | Pending |
| 3 | Strategy backtesting (backtesting.py) | Pending |
| 4 | Fundamental integration (CasualMarket) | Pending |
| 5 | Chip data + macro context (FinMind) | Pending |
| 6 | Stock screener + portfolio optimizer + scheduling | Pending |
| 7 | Factor validation + event study | Pending |
| 8 | Sentiment (Google Trends / pytrends) | Pending |
| 9 | Dashboard (Streamlit) | In progress |

---

## Data Sources

| Tool | Purpose |
|------|---------|
| [twstock](https://github.com/mlouielu/twstock) | Historical OHLCV, real-time quotes |
| [FinMind](https://finmind.github.io/) | Institutional flow, margin data, financial statements |
| [CasualMarket](https://github.com/sacahan/CasualMarket) | Financials, monthly revenue, dividends (MCP Server) |
| TWSE OpenAPI | Market breadth, official price data |
| yfinance | USD/TWD exchange rate |
| data.gov.tw | Taiwan business cycle indicators |

---

## References

- [locupleto/streamlit-lightweight-charts-v5](https://github.com/locupleto/streamlit-lightweight-charts-v5) (MIT) — Dashboard chart component
- [kevin801221/stock-strategies-only](https://github.com/kevin801221/stock-strategies-only) (MIT) — Taiwan stock screening logic and factor design reference

---

## License

[MIT](LICENSE)
