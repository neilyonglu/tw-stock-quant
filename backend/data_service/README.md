# 資料中台（data_service）

負責向外部來源（yfinance、twstock、FinMind）抓取 + 記憶體 TTL 快取資料，前端與後端都跟這裡要資料，
不要自己重打外部 API。完整背景見 [../../PROJECT.md](../../PROJECT.md)「架構：中台 / 前端 / 後端」。

## 啟動

```bash
uv run uvicorn backend.data_service.main:app --reload --port 8001
```

啟動後可以直接開 http://localhost:8001/docs 看互動式 API 文件（FastAPI 自動產生）。

## Endpoints

| Method | Path | 說明 | TTL |
|---|---|---|---|
| GET | `/health` | 存活檢查 | — |
| GET | `/stocks/search?q=` | 依代碼前綴或名稱關鍵字搜尋股票（只回一般股票，排除權證/ETF），回 `[{ticker, name}]` | 3600s |
| GET | `/stocks/{ticker}/candles?period=&interval=` | raw OHLCV + 成交量 + 漲跌停價（不含技術指標） | 60s |
| GET | `/stocks/{ticker}/profile` | 產業別/上市櫃別/本益比/股價淨值比/殖利率/EPS/52週高低/市值/股本/分析師目標價 | 1800s |
| GET | `/stocks/{ticker}/fundamentals?dataset=&start_date=&end_date=` | FinMind 原始損益／資產負債／現金流／月營收／股利；各次查一類 | 1800s |
| GET | `/stocks/{ticker}/orderbook` | 五檔委買委賣 | 30s |
| GET | `/stocks/{ticker}/intraday` | 今日 1 分鐘分時走勢 | 30s |
| GET | `/market/indices` | 加權指數/櫃買指數/道瓊/那斯達克/日經/上證 | 30s |
| GET | `/market/intraday` | 加權指數今日 1 分鐘分時走勢 | 30s |

`period`/`interval` 是 yfinance 的字串格式，例如 `period=6mo&interval=1d`、`period=1d&interval=5m`。

### 基本面原始資料

```text
GET /stocks/2330/fundamentals?dataset=income_statement&start_date=2022-01-01
GET /stocks/6488/fundamentals?dataset=monthly_revenue&start_date=2024-01-01
```

`dataset` 必填，支援以下五個值；起日預設「台北今年往前四年的 1 月 1 日」，
迄日預設台北今日。日期須符合 `start_date ≤ end_date ≤ 今日`，按上游 `date` 篩選。

| dataset | FinMind dataset | 用途 |
|---|---|---|
| `income_statement` | `TaiwanStockFinancialStatements` | 各期 EPS、淨利、營收與毛利等原始科目 |
| `balance_sheet` | `TaiwanStockBalanceSheet` | 資產、負債、權益等原始科目 |
| `cash_flow` | `TaiwanStockCashFlowsStatement` | 營業現金流、資本支出與股本交易等原始科目 |
| `monthly_revenue` | `TaiwanStockMonthRevenue` | 月營收本值，保留年份、月份與 `create_time` |
| `dividends` | `TaiwanStockDividend` | 股利政策、除息與付款日期，不等同已領取股息 |

成功回 `{ticker, source:"FinMind", dataset, start_date, end_date, fetched_at, records}`；
`dataset` 是上游完整名稱。`records` 依 `date` 升冪，原始列與欄位不做改名、縮放、
補零或比率計算；有效的 0、負值、null 與空字串均保留。`fetched_at` 是 UTC 抓取時間，
快取命中時保留原時間。實際科目完整度依個股與期間而異，拿到資料表不等於每項規則都可計算。

**期間與單位**：財報的 `date` 是報表期末，不是公告日；不可一律當作單季或直接年化。
月營收所屬月要看 `revenue_year`／`revenue_month`，例如 `date=2026-10-01` 可對應 9 月營收。
月營收 `create_time` 是 FinMind 入庫日，舊資料可能空字串，不是正式公告日。
一般金額以來源本值保留（常見為新台幣元），EPS／每股股利為元／股，其他科目可能是股數或比率；
計算前須核對科目與單位，不可對整張表統一乘千或除億。EPS 配股／分割的跨季股數基準也可能不同。
這是目前可取得的歷史資料，`end_date` **不提供當時可知資料的回測保證**。

沒有資料回 404；股票／日期／dataset 不合法回 404 或 422；上游限額回 503，
連線／授權／格式異常回 502，逾時回 504。失敗不快取、不回空成功、不自動補 mock。
每次僅查指定類型，沿用現有 TTL；尚未包含全市場批次與集中限速。

`FINMIND_TOKEN` 選填，只放 Authorization header。Docker Compose 讀根目錄 `.env`
並傳入中台；本機 uvicorn 不會自行載入 `.env`，有填 token 時改用：

```bash
uv run --env-file .env uvicorn backend.data_service.main:app --reload --port 8001
```

匿名額度耗盡或授權失敗會明確回報，不保證永久免金鑰可用。原 `/profile`、
前端月營收 mock 及選股頁均維持既有合約，此步只完成中台資料入口。
資料定義見 [FinMind 官方文件](https://finmind.github.io/tutor/TaiwanMarket/Fundamental/)。
兩市場官方公告抽查結果與已發現差異見 [基本面資料核對](../../docs/fundamental-data-review.md)；
原始入口尚未自動辨識公告更新延遲或阻擋跨來源差異，計算前必須處理這些限制。
計算層現提供 `uv run python -m backend.api.check_fundamentals 2330`，依人工查核紀錄回報
已知更新落後與數值差異；不改此 raw 合約，也不把未驗證資料當已通過篩選。

### 上市／上櫃與股票清單

個股路徑使用裸代碼，例如 `/stocks/2330/candles`、`/stocks/6488/candles`，不帶後綴。
共用 `backend.data.universe.yahoo_symbol()` 依已安裝的 `twstock.codes` 選上市 `.TW`、
上櫃 `.TWO`；K 線、前收盤、基本面、分時與 SQLite 鍵一致。五檔沿用 twstock 的裸代碼介面。
成功回傳欄位與 endpoints 不變；未知、帶後綴或不支援市場的代碼回 404 + `{"detail":"..."}`，
不再把未知代碼猜成上市或上櫃。新掛牌若不在本機表內，需先更新代碼表。

搜尋與 `backend.data.universe.stock_universe()` 共用一般股票清單，排除 ETF／權證／特別股及興櫃。
已知 ETF 等仍可經裸代碼直接查詢，僅不進入一般股票搜尋與選股清單。
清單函式回 `ticker`、`name`、`market`、`symbol`，按代碼排序；沒有另增 HTTP endpoint。
在根目錄執行 `uv run python -m backend.data.universe` 可離線印出上市／上櫃數量，這是安裝快照而非即時掛牌名單。

### 回傳格式的兩個注意事項（2026-07-29 起）

**1. 拿不到的數值一律是 `null`，不會是 `0`。** 這個系統的產出會影響真實投資決策，捏造一個看起來合法的 `0` 比留白危險。目前已知會是 `null` 的欄位：

- `/market/indices` 的 `otc`（櫃買指數整個物件）——yfinance 的 `^TWOII` 已查不到資料，在找到替代來源（TPEx OpenAPI）前一律 `null`
- `/stocks/{ticker}/candles` 的 `limit_up` / `limit_down`——取不到前一交易日收盤價時
- `/stocks/{ticker}/profile` 的各數值欄位（`market_cap`、`shares_outstanding`、`pe_ratio` 等）

**2. `candles` 多了 `stale_adjust` 欄位（布林）。** `true` 代表偵測到除權息、但整段重抓失敗，**這批價格仍是平移前的舊還原價**。拿去跑回測會得到錯的績效，請當作「這次資料不可信、稍後重取」處理。正常情況是 `false`。

另外，`limit_up`/`limit_down` 的計算基準一律是**前一交易日收盤價**，跟查詢的 `interval` 無關（看 5 分線和看日線拿到的漲跌停價相同）。

## 給後端（計算層）的邊界

中台**只做抓取 + 快取**，不算任何技術指標或評分。SMA/RSI/MACD、K 線型態辨識、選股評分、
投組優化這些「計算」都是後端的工作——跟中台要 raw candles，自己算完再回傳給前端。

錯誤一律回傳標準 HTTP 狀態碼（例如查無資料是 404 + `{"detail": "..."}`），不是 200 + `{"error": ...}`。

## 快取

兩層：

1. **記憶體 TTL**（`cache.py`）：依資料更新頻率分三級——近即時資料（五檔/分時/大盤指數）30s、
   K 線 60s、基本面 1800s。重啟清空、多實例不共享。
2. **SQLite 持久化**（`store.py`，`data/cache.db`，gitignored）：只存歷史日/週/月 K 線。
   重啟不掉；請求時只向 yfinance 增量要缺口（從庫存倒數 5 根重疊抓起），重疊處 close
   相對差 >0.1% 視為除權息還原價平移，該股整段重抓覆寫。分鐘 K 等即時資料不落地。

對外 HTTP contract 不受快取層影響，回傳格式與純現抓完全一致。

持久化 key 使用完整市場代碼，如 `2330.TW`、`6488.TWO`。不更動資料庫 schema，既有上市
快取沿用；上櫃只讀寫 `.TWO`，舊錯誤後綴的 `.TW` 資料不刪除、不視為上櫃快取。
