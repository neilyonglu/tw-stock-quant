# 專案脈絡

> 判斷現況以本檔 + `todo.md` 為準。未來 Phase 藍圖見 `plan.md`。
> 本檔只記「最終狀態」：同一主題後續有修改就直接改寫對應段落，不留流水帳。

## Docker 與自動部署

個股 Route Handler 以 `runPythonModule` 啟動 `backend.api.get_stock_data`，
共用 `backend/indicators/` 計算指標及真實 K 線型態；前端 JSON 欄位維持原合約。
`docker-compose.yaml` 以同一個 Node＋Python image 分別跑前端與中台，SQLite 掛 volume。
正式環境排除 research/dev 依賴，本機 `uv sync` 仍裝原有工具，套件鎖定版本不變。
`.github/workflows/deploy.yml` 在雲端跑離線測試、Docker build 與服務互通檢查，
main 通過後交給 `[self-hosted, Linux, X64, tw-stock]` runner，部署到
`/mnt/ssd/self-proj/tw-stock-quant` 的精確 SHA。設定與驗收見 `docs/MAINTAINERS.md`。
main CI 與 server 部署已驗證成功；2026-10-13 的 run 38337855813 已完成容器改名 PR #5 的部署。

## 指標目前狀態（2026-10-15）

個股頁指標串接與說明完成，含 KD／ATR 副圖、速查卡與 K 棒週期；缺值顯示 —，MACD／SMA 僅描述位置。中台 `stale_adjust` 已在共用組裝入口阻擋，API 回 503、前端隱藏舊資料並自動重試。23 個 Python 測試、前端／Docker 建置及手機／桌面流程通過。公開公式與參考計算已核對，指定券商逐筆比對仍需同批來源資料。詳見 [docs/indicator-review.md](docs/indicator-review.md)。

指標變更已由 [PR #7](https://github.com/neilyonglu/tw-stock-quant/pull/7) 合併 main，功能分支已刪除。分支 push 只跑 CI，合併 main 後通過 CI 才部署到 server，不能以本機驗證代替部署成功紀錄。頁面現為六層圖表，控制欄隱藏捲軸但仍可捲動。本機避開 Forge 的 3000，使用 3107 預覽，指令見 [部署與預覽文件](docs/MAINTAINERS.md#本機預覽與重新建置)。

## 股票清單與上市／上櫃來源（2026-10-16）

股票清單已由 PR #8 合併 main，功能分支已刪除。共用 `backend/data/universe.py` 讀取已安裝的 twstock 代碼表，提供一般股票清單與 `yahoo_symbol()` 市場解析；上市 `.TW`、上櫃 `.TWO`。K 線、前收盤、基本面、分時和 SQLite 快取鍵都使用同一解析，不再固定 `.TW`。搜尋沿用既有回傳欄位，改用同一清單。ETF／權證／特別股不進選股清單，已知 ETF 等直接查詢仍保留；未知或不支援市場回既有格式的 HTTP 404，不猜上市櫃別。

`uv run python -m backend.data.universe` 離線印出數量；目前安裝快照為上市 1045、上櫃 880，共 1925 檔，數量會隨代碼表更新，並非即時掛牌名單。沒有新增 HTTP endpoint、套件或批次掃描排程。既有正確 `.TW` 快取不需搬移，新增 `.TWO` 獨立儲存，舊錯誤後綴資料不自動刪除或挪用。

31 個 Python 測試通過，包含兩市場來源、快取隔離、未知代碼無網路即 404，以及 raw K 線到指標組裝。實際 2330／6488 搜尋、日 K、分時、基本面及指標驗收通過；正式 Docker 前端→中台的兩市場 smoke check 通過，測試使用獨立網路、暫存 SQLite 與 3108，不變更既有 3107 預覽。這些結果不代表所有股票資料都完整；下一步才是批次掃描與頻率控制。

## 單股技術篩選（2026-10-16）

單股技術篩選已在 `feature/technical-screening` 實作：`backend/screening/technical.py` 純計算，`backend/api/screen_stock.py` 經中台取一年日 K。固定 technical-v1 權重為趨勢 30／MACD 25／動能 25／量能 15／當根偏多型態 5，前四項必須全過，分數不代表勝率。金叉比較相鄰兩根；資料不足、異常或還原失敗回 null 分數及原因。CLI 保守排除台北日期的當日 K，含當日已收盤情況；輸出實際 `as_of`，不冒充今日訊號。55 項測試與兩市場真實資料／Docker CLI 驗收通過，規則與指令見 [technical-screening.md](docs/technical-screening.md)。批次掃描、多因子整合、賣出／持倉、回測與投組仍未實作，整體選股頁仍是示範資料。

## 目標

台灣股市量化系統：定期掃全市場 → 四層篩選出候選股（總體→基本面→籌碼→技術，見 plan.md）→ 投組優化配置 → GitHub Actions 定時執行 → Telegram 推播。不依賴付費黑盒子，完全自控。

目標使用者是一般大眾（投資與程式皆入門），介面設計原則：每個數字旁有一句白話說明、結論優先、支援手機。風格參考 Robinhood（消費者友善）+ Linear（深色排版）+ TradingView（K 線頁空間配置）。

## 架構：中台 / 前端 / 後端

Python 程式集中在 `backend/`：中台為 `backend/data_service/`，個股計算入口為
`backend/api/get_stock_data.py`；目錄圖與互動架構圖見 `docs/ARCHITECTURE.md`。
`store.py` 仍使用根目錄 `data/cache.db`，Docker 的 SQLite volume 與既有 API 維持原樣。

**中台是唯一向外部來源（yfinance/twstock/FinMind/…）抓資料的地方**，前端和後端都跟中台要資料。理由：前端要顯示、後端要計算，兩邊要的是同一份 raw 資料，各自抓會延遲疊加、邏輯分岔。

- **中台 `backend/data_service/`**：獨立 FastAPI 服務（`uv run uvicorn backend.data_service.main:app --reload --port 8001`，`/docs` 有互動文件）。只回 **raw 資料**，不算任何指標。快取兩層：記憶體 TTL（`cache.py`）三級——五檔/分時/指數 30 秒、K 線 60 秒、基本面 1800 秒；日/週/月 K 另落地 SQLite（`store.py`，`data/cache.db`，gitignored）——重啟不掉、只向 yfinance 增量要缺口、增量時重疊抓 5 根比對 close 偵測除權息（相對差 >0.1% 即整段重抓覆寫）。分鐘 K 等即時資料不落地。Endpoints 見 `backend/data_service/README.md`。**HTTP contract 是給後端隊友的穩定介面，改 endpoint 或回傳格式前一律先問使用者。**
- **前端 `frontend/`**：Next.js 16.2.9 + Tailwind v4 + shadcn/ui 4.12（`base-nova` style，底層 @base-ui 非 Radix）+ lightweight-charts v5。只負責顯示。三個頁面：`/market`（市場總覽）、`/stock/[ticker]`（個股分析）、`/screening`（每週選股）。
- **後端**（計算層）：`backend/indicators/` 提供共用 `add_indicators(df)`，計算 SMA/EMA/RSI/MACD/KD/ATR 與均量；數值指標使用 pandas，TA-Lib 用於型態辨識。`backend/api/get_stock_data.py` 組裝個股 JSON；`backend/screening/technical.py` 與 `backend/api/screen_stock.py` 提供單股技術規則、分數與理由。多因子選股、投組優化尚未實作；隊友另開 branch 負責回測。
- 本機開發：`./scripts/dev.sh` 同時啟動中台＋前端（Ctrl+C 一起關）。

### API 合約原則（接後端時的關鍵）

1. 前端元件（`*-view.tsx`）只透過 `fetch('/api/...')` 拿資料，不 import mock 物件、不直接呼叫 Python。
2. **Route Handler 回傳的 JSON 形狀＝未來後端 API 的合約**，單一定義來源在 `frontend/src/lib/types.ts`（每個 interface 上方標註「[真實]/[mock]」＋資料來源）。
3. 換資料來源（mock → 真後端）只改 Route Handler 內部，JSON 形狀不變，前端元件零改動。
4. 選股結果（`/api/screening`）**不經過中台**：評分/進場停損/配置% 是計算產出（後端工作範圍），不是中台該抓的 raw 資料。

### Python 環境（只有一個：`uv run` 的 `.venv`）

中台 `backend/data_service/` 與 Next.js Route Handler 呼叫的 `backend/api/get_stock_data.py` **都跑在專案 `.venv`**——`frontend/src/lib/run-python.ts` 用 `execFile("uv", ["run", "python", ...])` 執行，不再依賴系統 PATH 上的 `python3`（2026-09-20 改）。所以 TA-Lib 在兩邊都可用，K 線型態辨識不再有環境障礙，指標層扶正時直接接 `talib`。

踩坑：Windows 上 PATH 的 `python3` 常解析到 Microsoft Store 的 app-execution-alias stub，跑起來沒 stdout 也沒錯誤，只會讓呼叫端 `JSON.parse` 失敗——這就是改用 `uv run` 的原因，不要改回 `python3`。

twstock 股票代碼表會過期（新掛牌股票查不到名稱/產業別），需要時跑 `uv run python -c "import twstock; twstock.codes.fetch.__update_codes()"` 更新一次即可。twstock 用 PyPI 版（`>=1.5.1`），原本的本地 editable fork 已刪除。

## 已完成（快照）

- **環境**（2026-06-27）：Python 3.12 + uv、TA-Lib（source 編譯）、twstock、CasualMarket MCP；8 個 equity-research skills + `stock-analyst` dispatcher（Phase 4–6 會用）。
- **Dashboard 建皮 Step 0–5 全部完成**（2026-06-28 ～ 07-02）：三頁介面、五層 K 線疊圖（K 線+SMA20/60、成交量+MA5/10 均量線、RSI、MACD）、7 種時間週期（5/15/30/60 分、日/週/月）、個股頁 6 個 Tabs（分時/K 線/速查指標/籌碼/基本面/新聞）、五檔報價、選股表格+圓餅圖+CSV 下載、響應式（手機底部 nav／平板 icon bar／桌面完整 sidebar，375px 實測無溢出）。
- **中台拆分**（2026-07-01）：`backend/data_service/` 上線，前端 Route Handler 改打中台。
- **UI/UX 無障礙稽核修正**（2026-07-04）：對比度、44px 觸控目標、aria 標記、emerald 品牌色補齊（詳見下方慣例）。
- **前端 Dashboard 併入 main**（2026-07-22）：`feature/dashboard-ui` 經 PR #1 併回 main（merge commit）。同時 main 設了 branch protection ruleset：改 main 一律走 PR（禁直接 push）、禁 force-push、禁刪除，**不強制 review**（作者可自 merge）。日常流程＝branch → push → PR → merge。
- **中台快取持久化**（2026-07-23）：SQLite 兩層快取上線（細節見上方架構段）。驗收：改動前後回傳逐欄位比對、重啟後增量只抓 5 根（日/週/月三種週期實測）、污染庫內 close 觸發除權息路徑自我修復。
- **自選股清單＋定期自動刷新**（2026-07-29）：前端新增 `/watchlist` 頁面，個股頁標題旁加星星按鈕加入/移除；清單存瀏覽器 localStorage（單機使用，之後要跨裝置同步再換後端資料庫，見 `frontend/src/lib/watchlist.ts`）。市場總覽、個股頁面加背景自動刷新，頻率對齊中台快取 TTL（報價/指數 30 秒、K 線 60 秒），分頁在背景分頁時暫停、切回前景立刻補刷一次。驗收：Playwright 實測加入/移除/清單顯示/自動刷新網路請求時序、console 無錯誤。
- **自選股頁改 App 風格＋個股首頁排行榜＋K 線今日按鈕**（2026-07-29）：自選股頁面改成 iOS 股票 App 卡片式列表（名稱/代碼＋迷你走勢圖 sparkline＋價格/漲跌色塊），走勢圖吃 `/api/stock/[ticker]/intraday`（真實資料）；新增 `/stock` 首頁（未指定代碼時），顯示今日漲跌幅前五名（沿用市場總覽既有的 mock 排行榜資料，畫面明確標示「示範資料，非真實排行」，真資料要等全市場掃描 Phase 1+6），側邊欄「個股分析」改連到這裡而非固定 `/stock/2330`。K 線圖分頁的分鐘線加「今日」快速按鈕（period=1d）。過程中順手修掉 `backend/api/get_stock_data.py` 的一個既有 bug：資料筆數不足一個 RSI window（14 根）時 `.dropna().iloc[-1]` 會 IndexError 炸整支腳本（今日這種短區間會踩到），改成不足時退回中性值 50。
- **查無股票代碼的錯誤畫面**（2026-07-29）：搜尋不存在的代碼時，`get_stock_data.py` 原本會讓中台回的 404 直接讓 `urlopen` 拋出未接住的 `HTTPError`，整支腳本以 exit code 1 死掉；`run-python.ts` 的 `execFile` 一遇到非 0 exit code 就丟掉 stdout，前端只看得到通用的「Failed to fetch stock data」。修法：`_fetch_candles` 接住 404 轉成 `{"error": "查無股票代碼「X」..."}`，且這種「已處理的已知錯誤」改用 `sys.exit(0)`（不是腳本壞掉，只是查無資料，不該讓 stdout 被丟掉）。前端個股頁新增專用的查無代碼畫面（隱藏自選星星、不渲染分頁），取代原本混亂地在標題列塞一行紅字、下面 tabs 照樣試著渲染壞資料。
- **股票關鍵字搜尋 + 修掉切換代碼時的殘留資料 bug**（2026-07-29）：新增 `/stocks/search`（中台）→ `/api/stock/search`（前端代理），依代碼前綴或名稱關鍵字搜尋，資料源是 twstock.codes 本地代碼表（過濾只留一般股票，排除權證/ETF 等雜訊，1942 檔）。共用元件 `frontend/src/components/ticker-search.tsx`（debounce 200ms、下拉選單、方向鍵/Enter/Esc），個股頁側邊欄與 `/stock` 首頁的搜尋框都換成這個，不再各自維護一份。過程中發現並修掉一個真的 bug：切換股票代碼時 `data` state 沒有立刻清空，導致轉圈載入或查詢失敗的當下，標題列會殘留上一支股票的名稱/價格（看起來像新代碼查到了舊資料）；修法是非背景刷新（非 silent）的 fetch 一開始就清空 `data`，背景自動刷新不清（避免每次刷新都閃爍）。
- **全 repo 稽核與資料誠實性修正**（2026-07-29）：三份平行稽核（Python / 前端 / 文件）後修掉三條「假資料看起來像真的」——(1) 櫃買指數抓不到卻回 `0`，改成回 `null`＋UI 顯示「—」；(2) K 線型態每支股票都回同一筆假的「錘子線／偏多」，且跟真的 SMA/MACD/RSI 訊號並排顯示，改成不產生型態訊號；(3) 市場總覽六個區塊、籌碼面／新聞整頁、月營收等 mock 沒有任何視覺標示，建立共用 `mock-badge.tsx` 統一標記。做法已寫成上方「真實 vs mock 資料對照」的三條規則。稽核也記錄了未修的問題（白屏防護、漲跌停短區間算錯、race condition 等），見下一條。
- **稽核其餘 11 項全部修完**（2026-07-29）：
  - **漲跌停價算錯**（影響最大）：`_render()` 原本拿「輸出清單的倒數第二根」當前收盤價，但漲跌停是「日」的概念——看 5 分線時它拿前一根 5 分 K、看月線時拿上個月收盤當基準，同一支股票同一天會因為選了不同週期而顯示四種不同的漲跌停價（實測 2330 得到 2505/2455/2585/2650），只有日線碰巧對。改成新增 `_prev_daily_close()` 固定抓日線算，四種週期實測一致。取不到就回 `null`（合約改為 nullable）。
  - **RSI 演算法**：原本用簡單移動平均，市面平台（TradingView/券商）用 Wilder's smoothing，數字對不上會讓人以為系統算錯。改用 Wilder（種子＝前 14 根簡單平均，之後遞迴平滑），已對 Wilder 原著範例資料驗證（第 14/15/17 根完全吻合）。
  - **API 失敗白屏**：12 個元件補上 `res.ok` 檢查與錯誤畫面。另外注意**錯誤畫面不要直接渲染後端回傳的錯誤字串**（會把技術訊息丟給使用者），一律顯示自己寫的中文提示。
  - **race condition**：6 個依 ticker 抓資料的元件補上 AbortController。
  - 其餘：`fetch_profile()` 缺值 `0`→`None`（0 會被讀成「市值真的是 0 億」）；除權息重抓失敗時回應新增 `stale_adjust` 標記（原本只寫 server log，呼叫端無從得知這批是舊還原價）；`ttl_cache` 加 per-key 鎖防 cache stampede（實測同 key 並發 20 次只執行 1 次、不同 key 不互相阻塞）；只有 1 根 K 棒時的 IndexError（含 MACD 同類問題）；圖表色碼抽到 `frontend/src/lib/chart-colors.ts`（原本兩個圖表元件各複製一份）；`watchlist.ts` 移除 3 個沒用到的 export。
  - **刻意沒做**：稽核建議「把 `--stock-up/--stock-down` token 統一到所有漲跌顏色」——實際查證後發現這條建議是錯的。那組 token 是**圖表**用色（#EF5350/#26A69A），而畫面文字用的 `text-red-400`/`text-emerald-400` 是依 WCAG 對比度實測選的，兩者用途不同，硬統一會破壞無障礙合規。改為只把重複的圖表色碼集中，並在 `globals.css` 與 `chart-colors.ts` 兩邊都註記這個區別。
- **Route Handler 改用 `uv run` 執行 Python**（2026-09-20）：`run-python.ts` 從 `execFile("python3")` 改成 `execFile("uv", ["run", "python", ...])`。直接原因是 Windows PATH 上的 `python3` 會解析到 Store stub 導致靜默失敗；副作用是前端呼叫的腳本從此跑在專案 `.venv`，「兩個 Python 環境、TA-Lib 只在其中一邊」的問題一併消失（見上方「Python 環境」）。
- **archify 架構圖工具裝進專案**（2026-09-22）：`npx skills add tt-a1i/archify`（專案層級，非全域），落在 `.agents/skills/`，Claude Code 可用 `archify` skill 從文字描述產生可互動的架構圖 HTML。`.agents/` 與 `skills-lock.json` 是否進版控待定（見 todo.md）。

## 真實 vs mock 資料對照

**mock 絕對不能看起來像真的**——本系統產出投資決策，錯誤數據是安全問題。判斷標準：yfinance / twstock 免金鑰拿得到的就接真的，拿不到的用 mock 佔位但型別合約先定好。

這條規則有三個具體做法（2026-07-29 稽核後定案，改動 mock 相關畫面時照這個做）：

1. **畫面上每個 mock 區塊都要掛視覺標記**，用共用元件 `frontend/src/components/mock-badge.tsx`：`<MockBadge reason="等什麼資料源" />` 是行內小標籤（`<StatCard>` 直接傳 `mock` / `mockReason` prop），`<MockNotice>` 是整區/整頁都 mock 時的橫幅。
2. **抓不到資料就回 `null`，不要回 `0` 或任何「看起來合法」的預設值**——呼叫端負責顯示成「—」。捏造的 0 比空白危險得多（櫃買指數就是踩過這個坑）。
3. **不要生成假的「訊號」或「判斷」**。純數字佔位加標記還能接受，但「錘子線／偏多」這種會被當成建議的假結論一律不做，寧可空白（K 線型態辨識就是為此改成回空陣列）。

| 資料 | 狀態 | 來源 / 等什麼 |
|------|------|--------------|
| 加權指數、國際指數 | **真實** | yfinance `^TWII`/`^DJI`/`^IXIC`/`^N225`/`000001.SS` |
| 櫃買指數 | **無資料源** | yfinance `^TWOII` 已查不到（2026-07-29 實測 `^TWOII`/`^TWO`/`^TPEX` 全回 0 筆）。中台回 `null`、UI 顯示「—」，**不捏造 0**。要接真的得另找 TPEx OpenAPI，見 todo.md |
| 個股/大盤分時走勢（今日 1 分 K） | **真實** | yfinance `period=1d interval=1m` |
| 個股 K 線（7 種週期） | **真實** | 中台 ← yfinance |
| 個股 PE/PB/殖利率/市值/EPS/52 週高低/目標價 | **真實** | yfinance `Ticker.info` |
| 產業別、上市/上櫃 | **真實** | twstock 本地查表 |
| 五檔報價 | **真實** | `twstock.realtime.get()`（盤後 asks/bids 可能空陣列） |
| 漲跌停價 | **真實計算** | 前收盤 ±10% 依跳動單位取整 |
| USD/TWD、美債 10Y | mock（yfinance 其實拿得到，等 `/api/market` 其他欄位一起換） | `USDTWD=X`、`^TNX` |
| 景氣燈號、市場廣度、三大法人 | mock | Phase 1 + Phase 5（FinMind/data.gov.tw） |
| 個股籌碼（法人/融資券/大戶）、月營收 | mock | Phase 5 FinMind / Phase 4 CasualMarket |
| K 線型態辨識 | **真實計算** | `backend/indicators/pattern.py` 用 TA-Lib 辨識晨星／黃昏星／錘子線／上吊線／吞噬，只回最近 5 根；沒有訊號時回空陣列 |
| 台指期貨、外資未平倉 | mock | 無免費來源，要另找（券商 API） |
| 排行榜（類股/成交值/漲跌幅） | mock | 需全市場掃描，Phase 1+6 |
| 新聞（個股/大盤） | mock | 全市場新聞牆要另找來源 |
| 選股結果、投組配置 | mock | 自建計算層（評分/優化），Phase 藍圖見 plan.md |

## 關鍵決策

| 決策 | 原因 |
|------|------|
| 不用 FinLab | 付費，要完全自控 |
| 推播用 Telegram Bot | LINE Notify 已於 2025 停止服務 |
| 籌碼面用 FinMind | TWSE 官方 API 格式散，FinMind 整合好（免費 600 req/hr） |
| 事件研究自建（`statsmodels`+`scipy`） | PyPI 無現成台股套件，約 100 行 |
| Dashboard 用 Next.js（非 Streamlit） | 目標使用者是一般大眾，需手機支援與視覺公信力 |
| 部署規劃：前端 Vercel、後端 Railway/Render | 免費 tier 足夠 |
| 資料中台獨立成 `backend/data_service/`（FastAPI） | 前後端都要 raw 資料；隊友需要穩定的 HTTP contract，不該讀 Next.js 內部細節 |
| 快取持久化選 SQLite 不選 Parquet | 每日補 K 棒、除權息覆寫都是逐列 upsert，SQLite 天生支援；Parquet 一次寫整檔不適合快取，降級為未來回測匯出格式（2026-07-23） |
| 指標共用入口在 `backend/indicators/`，個股 wrapper 在 `backend/api/get_stock_data.py` | 個股頁與未來批次掃描共用計算，JSON 組裝不混入資料中台 |
| 深色主題寫死 `<html className="dark">`，不用 next-themes | 本來就沒有亮色 variant、沒有 toggle UI；系統偏好偵測整套用不到 |
| 選股表排序手刻 `useState`，不裝 TanStack Table | 只有 3 欄要排序；表格複雜度提高再換 |
| 正式排程用 GitHub Actions，APScheduler 僅本機測試 | 雲端免費、電腦關著也能跑 |
| Route Handler 用 `uv run python` 不用系統 `python3` | Windows PATH 的 `python3` 會解析到 Store stub 靜默失敗；順帶讓前後端共用同一個 `.venv`，TA-Lib 兩邊都可用（2026-09-20） |
| Phase 維持水平順序推進（1→2→…→6），不改成先跑通最小管線 | 2026-09-22 討論後決定；Phase 3 回測是隊友範圍，跳過而非重排 |
| PTT 情緒分析直接呼叫 Claude API | 不跑本地 NLP 模型 |

## 考量區（參考，尚未採用；2026-10-16）

參考 [Open-Dev-Society/OpenStock](https://github.com/Open-Dev-Society/OpenStock)。以下記錄可借鏡的產品設計，不視為新增需求或已排定開發，也不替代目前技術篩選的回測驗證。

| 可參考項目 | 對本專案的考量 |
|---|---|
| 個股資訊分區 | 圖表、技術摘要、財務、公司介紹分區，讓使用者容易找到數字與來源；整體選股接真資料時再評估摘要配置。 |
| 全域快捷搜尋 | OpenStock 提供 Cmd/Ctrl+K、搜尋防抖與預設熱門股票。現有代碼／名稱搜尋可先沿用，有跨頁操作需求時再考慮快捷入口。 |
| 個人自選股 | OpenStock 使用帳號與資料庫保存自選股；本專案目前為 localStorage，多裝置同步成為實際需求時再評估後端保存。 |
| 資料可用性呈現 | 依市場、資料商能力顯示可用資訊，圖表不可嵌入時提供外部連結；可借鏡其延遲行情、來源限制與缺資料狀態說明。 |

來源：[功能與架構](https://github.com/Open-Dev-Society/OpenStock#readme)、[個股頁實作](https://github.com/Open-Dev-Society/OpenStock/blob/main/app/%28root%29/stocks/%5Bsymbol%5D/page.tsx)、[市場限制](https://github.com/Open-Dev-Society/OpenStock/blob/main/MARKET_SUPPORT.md)。檢查的是目前 main，後續採用前仍需核對版本。

OpenStock 的技術面摘要使用 TradingView 的嵌入 widget，不是可直接沿用的 Python 選股引擎。它的市場支援文件也列出台灣嵌入 K 線及 Finnhub 免費報價限制。程式庫目前標示 [AGPL-3.0](https://github.com/Open-Dev-Society/OpenStock/blob/main/LICENSE)；本專案為 MIT，搬用程式前需確認授權相容性，介面構想參考與複製程式分開評估。

**TradingView 名詞區分**：

- [TradingView 網站](https://www.tradingview.com/)：線上看盤與分析平台，提供圖表、指標、篩選與社群。
- [Lightweight Charts](https://www.tradingview.com/lightweight-charts/)：TradingView 提供的圖表程式庫，本專案用它繪圖；行情由本專案中台供應，指標與分數由 Python 計算。
- TradingView widget：外部服務提供的可嵌入元件；OpenStock 個股頁使用它呈現圖表與技術摘要。
- [Technical Ratings](https://www.tradingview.com/support/solutions/43000614331-technical-ratings/)：公開的多指標評級規格，可考慮作評分對照基準；尚未採用。完整規格包含 26 項，不可用本專案現有少數指標就宣稱已完整對齊，也不等於已驗證的交易策略。

目前 technical-v1 的自訂權重仍是實驗設定。後續評估先比較規則來源、台股資料可取得性及回測方式，再決定是否保留、調整或採用其他評級；沒有因這次調查直接更換算法。

## 前端慣例與踩坑

**色彩**
- **紅漲綠跌**（台股慣例，與美股相反）：所有「代表漲跌方向」的顏色——K 線、成交量柱、MACD 柱、漲跌文字、法人買賣超、多空橫幅、SignalBadge——漲/多頭=紅、跌/空頭=綠（token：`--stock-up` 紅 / `--stock-down` 綠）。非方向性顏色（RSI 門檻線、景氣燈號五色、amber 警示）不套這條。
- 說明文字用語意 token `text-muted-foreground`（對比 6.9:1），**不要**寫 raw `text-zinc-500`（只有 3.7:1，WCAG AA 不過）。
- 品牌強調色 emerald：`--primary`=emerald-700（白字 5.49:1）、`--ring`=emerald-500、sidebar active 用 `--sidebar-primary`=emerald-400。這些是對比實測選的值，不要換成 emerald-600（3.77:1 不夠）。

**互動與無障礙**
- 使用者反覆點的控制項至少 44×44px（`h-11`）：代碼搜尋、週期/區間 ToggleGroup、sidebar 收合鈕。
- icon-only 按鈕加 `aria-label`；輸入框用 `<label htmlFor>`；可排序表頭加動態 `aria-sort`。
- 日期時間一律用 `lib/utils.ts` 的 `formatDateTime`/`formatTimeShort`/`formatDate`，不要直接 `toLocaleString("zh-TW")`（預設 12 小時制帶上午/下午、不補零）。

**shadcn/ui 4.12（底層 @base-ui，非 Radix）**
- ToggleGroup：`value` 是 `string[]`、單選是 `multiple={false}`（無 `type="single"`）、選中樣式用 `aria-pressed:` 前綴（無 `data-[state=on]:`）。

**lightweight-charts v5**
- 單一 chart 多 pane：`chart.addSeries(Series, opts, paneIndex)`＋`chart.panes()[i].setHeight()`，crosshair 自動同步。
- 標記用 `createSeriesMarkers(series, markers)`（不是舊版 `series.setMarkers`）。
- 時間軸一律以 **UTC** 顯示：分鐘線要用「假 UTC」技巧 `calendar.timegm(ts.timetuple())`（把台北壁鐘時間欄位當 UTC 算 epoch），顯示出來才是台北時間。日/週/月線用日期字串不受影響。
- 縮放下限用 `lib/chart-zoom-bound.ts` 的 `boundChartZoom()` 依資料筆數動態算 `minBarSpacing`（不能寫死常數）＋`fixLeftEdge`/`fixRightEdge`。

**資料層**
- yfinance 未收盤當天會多一筆 OHLC 全 NaN 的列，抓完立刻 `dropna`——NaN 進 JSON 會讓前端 `JSON.parse` 直接炸掉。
- yfinance 還原價尾數會抖 ±0.01（同一支 API 隔幾分鐘再打就可能變一位），是 Yahoo 端行為不是 bug；除權息偵測門檻 0.1% 遠大於抖動（約 0.001%），不會誤觸發。
- yfinance period 的左緣語意（SQLite 快取 serve 起點照這個做，2330 基準實測）：日線＝首根 >= 切點；週線＝含切點那週的週一；月線＝切點後下一個月初（切點是 1 號則含當月）。
- 指數 ticker（`^TWII` 等）分鐘線 Volume 全 0，`IntradayChart` 偵測到就不畫成交量子圖。

**開發環境**
- Turbopack persistent cache（Next 16.1+ 預設開）：dev 時出現詭異 hydration 警告且 overlay 帶 `(stale)` 標籤 → 是快取跟編輯中程式碼對不上，`pkill -f "next dev"` + `rm -rf .next` 重開即可，不要在程式碼裡找 bug。
- recharts `Pie` 要加 `isAnimationActive={false}`，否則 headless 截圖驗證會拍到動畫第一格（空圖）。
- 環境沒有 `chromium-cli`：驗證用 scratchpad `npm install playwright --no-save`（`~/.cache/ms-playwright` 已有 Chromium），不進專案 `package.json`。

## 工具索引

### 資料來源

| 工具 | 用途 | 備註 |
|------|------|------|
| `twstock` | 台股 K 線、即時報價、五檔 | PyPI 版；代碼表更新見上方「Python 環境」 |
| `yfinance` | K 線、指數、匯率（`USDTWD=X`）、美債（`^TNX`）、`Ticker.info` | 免金鑰；NaN 坑見上方 |
| `CasualMarket` | 財報、月營收、股利（MCP Server，stdio） | Phase 4 |
| `finmind` | 三大法人、融資券、股東結構 | 免費 600 req/hr；Phase 5 |
| `fredapi` | 美債備援 | 需 `FRED_API_KEY` |
| TWSE OpenAPI / data.gov.tw #6099 | 漲跌家數 / 景氣燈號 | `requests` 直打；Phase 5 |
| `feedparser` | TWSE 重大訊息 RSS | Phase 6 |

### 分析 / 基礎設施

| 工具 | 用途 |
|------|------|
| `TA-Lib` | 技術指標、61 種 K 線型態（source 編譯；`make` 單執行緒不加 `-j`；只在 uv venv） |
| `backtesting.py` | 策略回測（Phase 3） |
| `alphalens-reloaded` / `pyportfolioopt` | 因子分析（Phase 7）/ 投組優化（Phase 6） |
| `statsmodels` / `scipy` / `scikit-learn` | 事件研究、統計檢定（Phase 7+） |
| `pyarrow` | Parquet 匯出（回測資料集，需要時再用；快取已定案用 SQLite） |
| `apscheduler` / `python-telegram-bot` | 本機測試排程 / 推播（Phase 6） |
| `pytrends` | Google Trends 情緒（Phase 8） |
