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

Source layout: `frontend/` contains the Next.js UI and Route Handlers;
`backend/api/` contains Python stock calculations; `backend/data_service/`
contains the FastAPI service, market sources and caches. Docker/Compose entry
files remain at the root. See [Architecture](docs/ARCHITECTURE.md) for the directory
map and exported interactive diagram.

A web-based analysis dashboard built with **Next.js 16 + Tailwind v4 + shadcn/ui + TradingView lightweight-charts**, served alongside a Python data layer.

| Step | Page | Status |
|------|------|--------|
| 0 | Project scaffold (Next.js + shadcn + lightweight-charts) | ✅ Done |
| 1 | App shell (sidebar + 3-page routing) | ✅ Done |
| 2 | Stock analysis page — 6-pane chart (candles + SMA20/60, volume + MA5/10, RSI, MACD, KD, ATR), indicator help, 7 timeframes, intraday/fundamentals/chip/order-book/news tabs (real data where yfinance/twstock allow, mocked elsewhere) | ✅ Done |
| 3 | Market overview page — indices (real), institutional flows/breadth/rankings/futures/news (mocked pending Phase 1/4/5/6 backend) | ✅ Done |
| 4 | Weekly screening results page — sortable table, portfolio allocation pie chart, CSV export (mock data) | ✅ Done |
| 5 | Polish pass — dark theme hardcoded (dropped `next-themes`, no light variant needed), responsive sidebar (mobile bottom nav / tablet icon-bar / desktop full width), mobile layout fixes at 375px, chart zoom lower-bound (can't zoom past the actual data span), unified `zh-TW` date/time formatting, red-up/green-down color audit; follow-up UI/UX accessibility audit — contrast fixes, 44px touch targets, aria-labels/aria-sort, restored the emerald brand accent color | ✅ Done |

| 6 | Watchlist + live refresh — iOS-Stocks-style watchlist with intraday sparklines (stored in browser localStorage), background auto-refresh matching the data tier's cache TTLs (30s quotes / 60s K-line, paused while the tab is hidden), stock landing page with gainer/loser rankings, ticker **and company-name** keyword search with autocomplete, and an explicit "ticker not found" state | ✅ Done |

The stock page includes expandable indicator definitions, timeframe explanations and KD/ATR charts and cards. Missing readings show “—”; failed price adjustments stop calculations and return HTTP 503 until data recovers. Validation: 23 Python tests, a native Node indicator check, production/Docker builds and desktop/mobile browser checks. See [indicator review](docs/indicator-review.md) for numerical comparisons and platform differences.

See [PROJECT.md](PROJECT.md) for the full real-vs-mock data inventory per field.

**Every mocked figure on screen carries a visible "示範資料" (sample data) marker** — this system's output feeds real investment decisions, so sample data must never be mistakable for the real thing. Where a real source is unavailable the UI shows "—" rather than a plausible-looking fabricated number.

### Architecture: data tier / frontend / backend

Data fetching is owned by an independent **data tier** (`backend/data_service/`, FastAPI; in-memory TTL cache for realtime data + SQLite persistent cache for historical daily/weekly/monthly candles with incremental fetch and dividend-adjustment detection) — both the frontend (display) and the backend (computation: indicators, scoring, and portfolio optimization built in this repo; backtesting contributed from a teammate's branch) fetch raw data from it instead of hitting external APIs directly. See [backend/data_service/README.md](backend/data_service/README.md) for the API contract.

Local dev needs both the data tier and the frontend running. `./scripts/dev.sh` starts both with one command (Ctrl+C stops both); or run them separately:

```bash
uv run uvicorn backend.data_service.main:app --reload --port 8001   # data tier
cd frontend && npm run dev                                   # frontend
```

---

## Docker and automatic deployment

The image packages the frontend, data service and shared `backend/indicators/`
modules. Stock requests run `python -m backend.api.get_stock_data` in the frontend
container. The stock JSON includes KD/ATR series; failed price adjustments return
HTTP 503 with `stale_adjust: true` instead of prices and indicators.

```bash
docker compose -p tw-stock-quant up -d --build --wait
```

For local Windows preview alongside Forge or another service using port 3000:

```powershell
$env:PORT = "3107"
docker compose -p tw-stock-quant up -d --build --wait
```

Open http://localhost:3107/stock/2330 and check the chart's KD/ATR panes,
quick-reference cards and expandable help. Rebuild after pulling changes;
container port 3000 stays unchanged. See [local preview](docs/MAINTAINERS.md#本機預覽與重新建置)
for persistent port settings and verification steps.

The shared Node + Python image runs the frontend and data service separately.
Only `127.0.0.1:3000` is published; use an SSH tunnel or HTTPS reverse proxy for
remote access. SQLite persists in the `stock-data` volume; `down -v` deletes it.
Local `data/cache.db` is not automatically migrated. Research/dev dependencies
are excluded from the image; local `uv sync` still installs the existing tools.
Builds need access to registries and Google Fonts; live quotes need their sources.
Before public deployment, update Next.js 16.2.9, which has critical npm audit findings.

All pushes run cloud CI. Successful main runs deploy through the server's
self-hosted runner labelled `tw-stock`, at `/mnt/ssd/self-proj/tw-stock-quant`.
See [MAINTAINERS.md](docs/MAINTAINERS.md) for setup and verification.

```bash
docker compose -p tw-stock-quant exec -T frontend python - < scripts/check_deployment.py
```

This optional full smoke check requires a reachable market data source.

The stock universe and market suffix resolver share the installed `twstock.codes`
snapshot. Candles, intraday data, profiles and SQLite keys use `.TW` for TWSE and
`.TWO` for TPEX. Search and the universe include ordinary shares only; known ETFs
remain available through direct requests. Unknown or unsupported market codes
return 404 instead of guessing an exchange. New listings require an updated code table.

```bash
uv run python -m backend.data.universe
```

This offline command prints the listed/OTC counts. Python callers can use
`stock_universe()` from `backend.data.universe` to obtain sorted
`ticker`, `name`, `market` and `symbol` records. The live deployment smoke check
covers both 2330 (TWSE) and 6488 (TPEX); bulk scanning is a later step.

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment setup | ✅ Done |
| 1 | Data pipeline — full-market scan | Universe + TWSE/TPEX routing implemented; SQLite already available. Bulk scanning and rate control remain. |
| 2 | Technical indicators | Implemented and connected, including KD/ATR, help and adjustment-quality handling. Reference checks pass; exact broker-screen matching requires identical source data — see [indicator review](docs/indicator-review.md). |
| 3 | Strategy backtesting (backtesting.py) | Teammate's scope (separate branch) |
| 4 | Fundamental integration (CasualMarket) | Pending |
| 5 | Chip data + macro context (FinMind) | Pending |
| 6 | Stock screener + portfolio optimizer + scheduling | Pending |
| 7 | Factor validation + event study | Pending |
| 8 | Sentiment (Google Trends / pytrends) | Pending |
| 9 | Data service (FastAPI) | ✅ Done — `backend/data_service/` on port 8001 |

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
