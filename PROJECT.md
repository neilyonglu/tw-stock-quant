# 專案脈絡

> 判斷現況以本檔 + `todo.md` 為準。未來 Phase 藍圖見 `plan.md`。
> 本檔只記「最終狀態」：同一主題後續有修改就直接改寫對應段落，不留流水帳。

## 目標

台灣股市量化系統：定期掃全市場 → 四層篩選出候選股（總體→基本面→籌碼→技術，見 plan.md）→ 投組優化配置 → GitHub Actions 定時執行 → Telegram 推播。不依賴付費黑盒子，完全自控。

目標使用者是一般大眾（投資與程式皆入門），介面設計原則：每個數字旁有一句白話說明、結論優先、支援手機。風格參考 Robinhood（消費者友善）+ Linear（深色排版）+ TradingView（K 線頁空間配置）。

## 架構：中台 / 前端 / 後端

**中台是唯一向外部來源（yfinance/twstock/FinMind/…）抓資料的地方**，前端和後端都跟中台要資料。理由：前端要顯示、後端要計算，兩邊要的是同一份 raw 資料，各自抓會延遲疊加、邏輯分岔。

- **中台 `data_service/`**：獨立 FastAPI 服務（`uv run uvicorn data_service.main:app --reload --port 8001`，`/docs` 有互動文件）。只回 **raw 資料**，不算任何指標。快取兩層：記憶體 TTL（`cache.py`）三級——五檔/分時/指數 30 秒、K 線 60 秒、基本面 1800 秒；日/週/月 K 另落地 SQLite（`store.py`，`data/cache.db`，gitignored）——重啟不掉、只向 yfinance 增量要缺口、增量時重疊抓 5 根比對 close 偵測除權息（相對差 >0.1% 即整段重抓覆寫）。分鐘 K 等即時資料不落地。Endpoints 見 `data_service/README.md`。**HTTP contract 是給後端隊友的穩定介面，改 endpoint 或回傳格式前一律先問使用者。**
- **前端 `frontend/`**：Next.js 16.2.9 + Tailwind v4 + shadcn/ui 4.12（`base-nova` style，底層 @base-ui 非 Radix）+ lightweight-charts v5。只負責顯示。三個頁面：`/market`（市場總覽）、`/stock/[ticker]`（個股分析）、`/screening`（每週選股）。
- **後端**（計算層）：技術指標、K 線型態、選股評分、投組優化由**本專案自行開發**；隊友另開 branch 只負責**回測系統**（2026-07-23 確認分工）。`src/api/get_stock_data.py`（跟中台要 raw candles，本地算 SMA/RSI/MACD）原定隊友 merge 後刪除，現改為指標層起點，待扶正為正式模組（見 todo.md）。
- 本機開發：`./scripts/dev.sh` 同時啟動中台＋前端（Ctrl+C 一起關）。

### API 合約原則（接後端時的關鍵）

1. 前端元件（`*-view.tsx`）只透過 `fetch('/api/...')` 拿資料，不 import mock 物件、不直接呼叫 Python。
2. **Route Handler 回傳的 JSON 形狀＝未來後端 API 的合約**，單一定義來源在 `frontend/src/lib/types.ts`（每個 interface 上方標註「[真實]/[mock]」＋資料來源）。
3. 換資料來源（mock → 真後端）只改 Route Handler 內部，JSON 形狀不變，前端元件零改動。
4. 選股結果（`/api/screening`）**不經過中台**：評分/進場停損/配置% 是計算產出（後端工作範圍），不是中台該抓的 raw 資料。

### 兩個 Python 環境（容易踩的坑）

1. `uv run` 的 `.venv`：`data_service/` 跑在這裡，TA-Lib **只**裝在這裡。
2. Next.js Route Handler `execFile("python3", ...)` 用的系統 python3（miniconda）：`src/api/get_stock_data.py` 跑在這裡，**沒有 TA-Lib**（所以 K 線型態辨識目前是 mock）。

twstock 股票代碼表會過期（新掛牌股票查不到名稱/產業別），需要時跑 `twstock.codes.fetch.__update_codes()` 更新——**兩個環境要各自跑一次**。twstock 用 PyPI 版（`>=1.5.1`），原本的本地 editable fork 已刪除。

## 已完成（快照）

- **環境**（2026-06-27）：Python 3.12 + uv、TA-Lib（source 編譯）、twstock、CasualMarket MCP；8 個 equity-research skills + `stock-analyst` dispatcher（Phase 4–6 會用）。
- **Dashboard 建皮 Step 0–5 全部完成**（2026-06-28 ～ 07-02）：三頁介面、五層 K 線疊圖（K 線+SMA20/60、成交量+MA5/10 均量線、RSI、MACD）、7 種時間週期（5/15/30/60 分、日/週/月）、個股頁 6 個 Tabs（分時/K 線/速查指標/籌碼/基本面/新聞）、五檔報價、選股表格+圓餅圖+CSV 下載、響應式（手機底部 nav／平板 icon bar／桌面完整 sidebar，375px 實測無溢出）。
- **中台拆分**（2026-07-01）：`data_service/` 上線，前端 Route Handler 改打中台。
- **UI/UX 無障礙稽核修正**（2026-07-04）：對比度、44px 觸控目標、aria 標記、emerald 品牌色補齊（詳見下方慣例）。
- **前端 Dashboard 併入 main**（2026-07-22）：`feature/dashboard-ui` 經 PR #1 併回 main（merge commit）。同時 main 設了 branch protection ruleset：改 main 一律走 PR（禁直接 push）、禁 force-push、禁刪除，**不強制 review**（作者可自 merge）。日常流程＝branch → push → PR → merge。
- **中台快取持久化**（2026-07-23）：SQLite 兩層快取上線（細節見上方架構段）。驗收：改動前後回傳逐欄位比對、重啟後增量只抓 5 根（日/週/月三種週期實測）、污染庫內 close 觸發除權息路徑自我修復。

## 真實 vs mock 資料對照

**mock 絕對不能看起來像真的**——本系統產出投資決策，錯誤數據是安全問題。判斷標準：yfinance / twstock 免金鑰拿得到的就接真的，拿不到的用 mock 佔位但型別合約先定好。

| 資料 | 狀態 | 來源 / 等什麼 |
|------|------|--------------|
| 加權指數、櫃買指數、國際指數 | **真實** | yfinance `^TWII`/`^TWOII`/`^DJI` 等 |
| 個股/大盤分時走勢（今日 1 分 K） | **真實** | yfinance `period=1d interval=1m` |
| 個股 K 線（7 種週期） | **真實** | 中台 ← yfinance |
| 個股 PE/PB/殖利率/市值/EPS/52 週高低/目標價 | **真實** | yfinance `Ticker.info` |
| 產業別、上市/上櫃 | **真實** | twstock 本地查表 |
| 五檔報價 | **真實** | `twstock.realtime.get()`（盤後 asks/bids 可能空陣列） |
| 漲跌停價 | **真實計算** | 前收盤 ±10% 依跳動單位取整 |
| USD/TWD、美債 10Y | mock（yfinance 其實拿得到，等 `/api/market` 其他欄位一起換） | `USDTWD=X`、`^TNX` |
| 景氣燈號、市場廣度、三大法人 | mock | Phase 1 + Phase 5（FinMind/data.gov.tw） |
| 個股籌碼（法人/融資券/大戶）、月營收 | mock | Phase 5 FinMind / Phase 4 CasualMarket |
| K 線型態辨識 | mock | TA-Lib 不在 route handler 的 python 環境（見上方兩個環境） |
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
| 資料中台獨立成 `data_service/`（FastAPI） | 前後端都要 raw 資料；隊友需要穩定的 HTTP contract，不該讀 Next.js 內部細節 |
| 快取持久化選 SQLite 不選 Parquet | 每日補 K 棒、除權息覆寫都是逐列 upsert，SQLite 天生支援；Parquet 一次寫整檔不適合快取，降級為未來回測匯出格式（2026-07-23） |
| 指標計算起點在 `src/api/get_stock_data.py`，待扶正為正式模組 | 原定隊友後端涵蓋所有計算、merge 後刪除佔位層；2026-07-23 確認隊友只做回測，指標/評分/優化歸本專案 |
| 深色主題寫死 `<html className="dark">`，不用 next-themes | 本來就沒有亮色 variant、沒有 toggle UI；系統偏好偵測整套用不到 |
| 選股表排序手刻 `useState`，不裝 TanStack Table | 只有 3 欄要排序；表格複雜度提高再換 |
| 正式排程用 GitHub Actions，APScheduler 僅本機測試 | 雲端免費、電腦關著也能跑 |
| PTT 情緒分析直接呼叫 Claude API | 不跑本地 NLP 模型 |

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
| `twstock` | 台股 K 線、即時報價、五檔 | PyPI 版；代碼表更新見上方「兩個 Python 環境」 |
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
