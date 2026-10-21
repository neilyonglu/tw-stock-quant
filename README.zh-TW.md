# tw-stock-quant

繁體中文 | [English](README.md)

台灣股市（上市／上櫃）個人量化研究 Dashboard。目前提供行情、技術指標、單股研究計算與資料品質檢查。全市場選股、投組優化、定時排程與 Telegram 推播仍在規劃中。

> **免責聲明**：本專案僅供個人學習與研究，不構成任何投資建議。

---

## 功能

| 狀態 | 功能 |
|------|------|
| 已接真資料 | 個股 K 線與技術指標、自選股、搜尋及可取得的大盤指數 |
| 研究計算 | 單股技術條件與評分、EPS、TTM ROE、營收 YoY、F-score，保留品質限制。四檔股票有人工年度補充；已驗證合格判定仍為未知。 |
| 示範介面 | 每週選股結果與投組配置、市場廣度、法人、期貨及新聞 |
| 規劃中 | 全市場與多因子選股、籌碼分析、投組優化、週五排程及 Telegram 推播 |
| 獨立分支 | 隊友負責策略回測，待整合 |

已安裝的 `backtesting.py`、`pyportfolioopt`、TA-Lib 是研究工具，不代表各項指標及流程已接入 Dashboard。

基本面警示區分業績摘要與完整核閱財報，並顯示來源實際期別；必要資料未取得前，受影響條件仍暫不判定。

---

## 安裝

先安裝 Git、[uv](https://docs.astral.sh/uv/)、Python 3.12 以上及含 npm 的 Node.js 22。Docker 建置也使用 Node.js 22。`uv sync` 安裝 Python 依賴；前端依賴另由 `npm ci` 按 lockfile 安裝。

```bash
git clone https://github.com/neilyonglu/tw-stock-quant.git
cd tw-stock-quant
uv sync
npm --prefix frontend ci
```

需要時複製 `.env.example` 為 `.env`，API key 均為選填；未填 token 時 FinMind 使用匿名額度，限額或來源失敗會明確回報。本機載入 token 使用 `uv run --env-file .env uvicorn backend.data_service.main:app --reload --port 8001`；Docker Compose 會自動傳入。

---

## Dashboard

個股頁已加入可展開的指標定義、週期說明及 KD／ATR 圖表與速查卡。缺值顯示 —，價格還原失敗時停止計算、回傳 HTTP 503，資料恢復後自動更新。當時指標驗收包含 Python 測試、原生 Node 檢查、正式／Docker 建置及桌面／手機檢查。目前 Python 測試請執行 `uv run pytest -q`。數值對照與平台差異見[指標檢查報告](docs/indicator-review.md)。

程式目錄：`frontend/` 放 Next.js 頁面與 Route Handlers；`backend/api/` 放 Python
個股計算；`backend/data_service/` 放 FastAPI 中台、資料來源與快取。Docker／Compose
入口維持在根目錄。目錄樹與可互動架構圖見 [架構說明](docs/ARCHITECTURE.md)。

以 **Next.js 16 + Tailwind v4 + shadcn/ui + TradingView lightweight-charts** 建立的網頁分析介面，搭配 Python 資料層。

| 步驟 | 頁面 | 狀態 |
|------|------|------|
| 0 | 專案初始化（Next.js + shadcn + lightweight-charts） | ✅ 完成 |
| 1 | app 框架（側欄 + 三頁路由） | ✅ 完成 |
| 2 | 個股分析頁 — 六層圖表（K 線＋SMA20/60、成交量＋MA5/10、RSI、MACD、KD、ATR）、指標說明、7 種時間週期、分時/基本面/籌碼面/五檔/新聞 Tabs（yfinance/twstock 拿得到的用真資料，拿不到的先 mock） | ✅ 完成 |
| 3 | 市場總覽頁 — 大盤/國際指數（真資料）、三大法人/市場廣度/排行榜/期貨/新聞（mock，待 Phase 1/4/5/6 後端） | ✅ 完成 |
| 4 | 每週選股結果頁 — 可排序表格、投組配置圓餅圖、CSV 下載（mock 資料） | ✅ 完成 |
| 5 | 收尾細節 — 深色主題寫死（拿掉 `next-themes`，本來就沒有亮色 variant）、Sidebar 響應式（手機底部 nav／平板 icon bar／桌面完整版）、375px 版面修正、圖表縮放下限（不能縮出資料範圍外）、日期時間格式統一成 `zh-TW`、紅漲綠跌色彩審查；後續 UI/UX 無障礙稽核——對比度修正、觸控目標放大到 44px、aria-label／aria-sort、補回 emerald 品牌強調色 | ✅ 完成 |

| 6 | 自選股 + 定期刷新 — 仿 iOS 股票 App 的自選股清單（含當日走勢迷你圖，存在瀏覽器 localStorage）、背景自動刷新（頻率對齊中台快取 TTL：報價 30 秒／K 線 60 秒，分頁切到背景時暫停）、個股首頁漲跌幅排行、支援**代碼與名稱關鍵字**的搜尋自動完成、查無代碼的專用錯誤畫面 | ✅ 完成 |

完整的「哪些欄位是真資料、哪些是 mock」對照表，見 [PROJECT.md](PROJECT.md)。

示範區塊必須標示「示範資料」。示範的市場方向或投組配置不是計算後的操作建議。真實來源缺值時顯示「—」。

### 架構：中台 / 前端 / 後端

執行 `uv run python -m backend.api.check_fundamentals 2330` 可查看實際期間及人工核對的已知差異。未知資料維持尚未驗證，這是品質報告，尚非選股結果；見[資料品質文件](docs/fundamental-data-review.md)。
執行 `uv run python -m backend.api.screen_fundamental 6488` 可查看四季 EPS、TTM ROE、三個月營收 YoY 與 F-score 九項訊號。2330／6488／2409／3481 的 2025／2024 年度已由官方財報人工核對補足長債與普通股發行，其他股票／年度缺項仍留空；最終已驗證合格判定保持 null，見[計算定義](docs/fundamental-screening.md)。
個股「基本面」已呈現上述指標、可展開九項訊號、真實六個月營收、期間與品質提示，註明人工核對年度資料並處理失敗／重試；每週選股頁仍是示範資料。文件整理了公式、操作、來源證據與驗證範圍，方便後續回查與討論。

執行 `uv run python -m backend.api.audit_financials 2409 3481 1303 --year 2025`，可透過中台取得官方年度財報、比對可取得的 FinMind 借款／公司債並合併例外。`--all` 可查本機一般股票名單；官方原件保存在 SQLite 並快取 24 小時，選股判定仍阻擋。見[批次查證](docs/fundamental-data-review.md#官方年度文件批次查證)。

查核報告包含兩年度普通股變動明細與期初、變動、期末勾稽。明確的普通股發行正值保留為證據；發行列缺席或股本不變均不足以證明未發行。這些報告不會更新 F-score 補充資料。

中台已可取得 FinMind 原始損益表、資產負債表、現金流量表、月營收及股利，例如 `/stocks/2330/fundamentals?dataset=income_statement`。類型與日期限制見 [API 合約](backend/data_service/README.md#基本面原始資料)；全市場已驗證基本面候選清單尚待完成。

**中台**（`backend/data_service/`，FastAPI）負責抓取外部資料。即時資料用記憶體 TTL 快取；歷史日／週／月 K 與官方財報原件版本保存在 SQLite。K 線增量抓缺口並偵測除權息還原。前端負責顯示，後端計算指標及單股研究結果；投組優化待開發，回測由隊友 branch 貢獻。前後端都向中台取得 raw 資料。API contract 見 [backend/data_service/README.md](backend/data_service/README.md)。

先完成 Python 與前端依賴安裝，再同時啟動中台與前端。Bash 可用 `./scripts/dev.sh` 啟動兩個服務，Ctrl+C 一起關閉。也可以在兩個終端機分別執行：

```bash
uv run uvicorn backend.data_service.main:app --reload --port 8001   # 中台
npm --prefix frontend run dev                                  # 前端
```

---

## Docker 與自動部署

image 包含前端、中台及共用的 `backend/indicators/`。個股請求在前端容器以
`python -m backend.api.get_stock_data` 執行。個股 JSON 新增 KD／ATR 序列；價格還原失敗時
回傳 HTTP 503 與 `stale_adjust: true`，不提供舊價格和指標。

```bash
docker compose -p tw-stock-quant up -d --build --wait
```

本機 Windows 若有 Forge 等服務使用 3000，改用 3107 預覽：

```powershell
$env:PORT = "3107"
docker compose -p tw-stock-quant up -d --build --wait
```

開啟 http://localhost:3107/stock/2330 ，查看 KD／ATR 副圖、速查卡及可展開的說明。
拉取修改後需重新建置；容器內部仍使用 3000。固定 port 與驗收步驟見
[本機預覽](docs/MAINTAINERS.md#本機預覽與重新建置)。

同一個 Node＋Python image 分別跑前端與中台，只公開 `127.0.0.1:3000`，遠端使用可接
SSH tunnel 或 HTTPS reverse proxy。SQLite 存於 `stock-data` volume，`down -v` 會刪除；
本機 `data/cache.db` 不會自動搬入。image 排除 research/dev 依賴，本機 `uv sync` 仍裝原有工具。
建置需連線 registry 與 Google Fonts，行情需連線外部來源。
公開部署前需升級 Next.js 16.2.9，它在 npm audit 有 critical 告警。

所有 push 都跑雲端 CI；main 通過後，由 server 的 `tw-stock` self-hosted runner
部署到 `/mnt/ssd/self-proj/tw-stock-quant`。設定與驗收見 [MAINTAINERS.md](docs/MAINTAINERS.md)。

```bash
docker compose -p tw-stock-quant exec -T frontend python - < scripts/check_deployment.py
```

此選用的完整檢查需要連到真實行情來源。

股票清單與市場代碼共用已安裝的 `twstock.codes` 快照。K 線、分時、基本面與 SQLite
快取鍵依市場選擇上市 `.TW`、上櫃 `.TWO`。搜尋與選股清單只含一般股票，已知 ETF
仍可直接查詢；查無代碼或市場不支援時回 404，不猜後綴。新掛牌需先更新代碼表。

```bash
uv run python -m backend.data.universe
```

此離線指令印出上市／上櫃檔數；Python 可呼叫 `backend.data.universe.stock_universe()`，
取得按代碼排序的 `ticker`、`name`、`market`、`symbol` 記錄。真實部署 smoke check
涵蓋上市 2330 與上櫃 6488；批次掃描尚未實作。

---

## 開發路線

中台啟動後，可用 `uv run python -m backend.api.screen_stock 2330` 執行單股日線技術篩選，
輸出五項條件、0–100 規則符合度與無法評分狀態。CLI 排除當日 K（即使當天已收盤），請看
`as_of` 評分日期；不取代示範選股頁，也不表示策略已驗證。規則與 Docker 指令見
[技術篩選 v1](docs/technical-screening.md)。

| 階段 | 說明 | 狀態 |
|------|------|------|
| 0 | 環境建置 | ✅ 完成 |
| 1 | 資料管線 — 全市場掃描 | 股票清單與上市／上櫃來源已實作，沿用 SQLite；批次掃描與頻率控制待做 |
| 2 | 技術指標 | 計算與串接完成，含 KD／ATR、說明及還原品質處理；參考對照通過，券商逐筆對齊仍需相同來源資料，見[指標檢查報告](docs/indicator-review.md) |
| 3 | 策略回測（backtesting.py） | 隊友負責（另一條 branch） |
| 4 | 基本面整合（FinMind） | 個股研究 UI 與月營收已換真；四檔指定年度補齊 F-score，全市場驗證待完成 |
| 5 | 籌碼面 + 總體環境（FinMind） | 待開始 |
| 6 | 選股系統 + 投組優化 + 排程推播 | 單股技術規則／分數／理由已實作；批次、多因子、投組與排程待做 |
| 7 | 因子驗證 + 事件研究 | 待開始 |
| 8 | 情緒面（Google Trends / pytrends） | 待開始 |
| 9 | 資料中台（FastAPI） | ✅ 完成 — `backend/data_service/`，port 8001 |

---

## 資料來源

| 工具 | 用途 |
|------|------|
| [twstock](https://github.com/mlouielu/twstock) | 台股歷史 OHLCV、即時報價 |
| [FinMind](https://finmind.github.io/) | 三大法人、融資券、財務報表 |
| [CasualMarket](https://github.com/sacahan/CasualMarket) | 選用 MCP 研究工具；執行期基本面資料改由 FinMind 取得 |
| TWSE OpenAPI | 漲跌家數、官方行情 |
| yfinance | USD/TWD 匯率、美債殖利率 |
| data.gov.tw | 台灣景氣燈號 |

---

## 參考來源

- [locupleto/streamlit-lightweight-charts-v5](https://github.com/locupleto/streamlit-lightweight-charts-v5) (MIT)
- [kevin801221/stock-strategies-only](https://github.com/kevin801221/stock-strategies-only) (MIT)

---

## 授權

[MIT](LICENSE)
