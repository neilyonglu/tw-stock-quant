# tw-stock-quant

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

## Roadmap

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
| yfinance | USD/TWD exchange rate, US treasury yield |
| data.gov.tw | Taiwan business cycle indicators |

---

## References

- [locupleto/streamlit-lightweight-charts-v5](https://github.com/locupleto/streamlit-lightweight-charts-v5) (MIT)
- [kevin801221/stock-strategies-only](https://github.com/kevin801221/stock-strategies-only) (MIT)

---

## License

[MIT](LICENSE)
