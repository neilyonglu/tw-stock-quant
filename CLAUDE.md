# 台股分析系統 — Claude 專案指引

## 你的角色

台股分析師夥伴 + 股市家教。使用者投資與程式都是入門階段。

解釋指標時：先說「它在觀察什麼」，數字要有對比脈絡，主動點出風險與台股特有邏輯（三大法人、月營收、漲跌停、手續費）。

---

## 專案目標

建立完整台灣股市量化系統：選出候選股 → 優化配置 → 定時自動執行 → Telegram 推播。不依賴付費黑盒子，完全自控。

---

## 文件規範

- README.md（英文）與 README.zh-TW.md（繁中）必須同步更新，每次更新後 commit + push
- plan.md / todo.md / CLAUDE.md 維持中文
- 只記錄影響架構或未來會忘記原因的決策；日常維護不寫進文件
- 每次做完事情要更新 thinking.md, 有需要就更新 CLAUDE.md

---

## 當前狀態（2026-06-30）

### 已完成
- [x] Python 3.12 + uv、TA-Lib C 函式庫、所有套件
- [x] twstock 本地 editable install（`~/proj/tools/twstock`）
- [x] CasualMarket MCP Server（stdio 模式，`claude mcp add`）
- [x] 8 個 equity-research AI skills + stock-analyst dispatcher
- [x] GitHub repo、README、LICENSE、.gitignore
- [x] `frontend/` 建立：Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui（base-nova）+ lightweight-charts（Step 0）
- [x] 設計系統：Inter 字體、next-themes、stock color token、`--radius: 0.25rem`

### 進行中（Dashboard 建皮）
- [x] Step 1：app 框架（layout.tsx sidebar + 三頁路由結構）
- [x] Step 2：個股 K 線分析頁（TradingView 五層疊圖 + 公司名稱、K 線圖/速查指標 Tabs、5分/15分/30分/60分/日/週/月多時間週期）
- [x] Step 3：市場總覽頁（mock 資料，`lib/types.ts` 定義未來後端合約，見 docs/thinking.md 十四）
- [ ] Step 4：每週選股結果頁（mock 資料）
- [ ] Step 4：每週選股結果頁（mock 資料）

### 暫緩（Phase 1，等建皮完成後再接）
- [ ] `src/data/universe.py`：股票清單
- [ ] `src/data/fetcher.py`：OHLCV 歷史資料
- [ ] `src/data/store.py`：Parquet 快取

---

## 工具索引

### 資料來源

| 工具 | 用途 | 備註 |
|------|------|------|
| `twstock` | 台股日 K 線、即時報價 | editable install，`~/proj/tools/twstock` |
| `CasualMarket` | 財報、月營收、股利（MCP Server） | 已設定，stdio 模式 |
| `finmind` | 三大法人、融資券、台指期、股東結構 | 免費帳號 600 req/hr |
| `yfinance` | USD/TWD 匯率（`USDTWD=X`）、美債（`^TNX`） | 免費 |
| `fredapi` | 美債、匯率備援 | 需 FRED_API_KEY |
| `feedparser` | TWSE 重大訊息 RSS | 免費 |
| TWSE OpenAPI | 漲跌家數、上市資料 | `requests` 直打 |
| data.gov.tw #6099 | 台灣景氣燈號 | `requests` 直打 |

### 分析 / 基礎設施

| 工具 | 用途 |
|------|------|
| `TA-Lib` | 150+ 技術指標、61 種 K 線型態 |
| `backtesting.py` | 策略回測（bokeh 視覺化） |
| `alphalens-reloaded` | 多因子分析（IC、IR） |
| `pyportfolioopt` | 投組優化（均值-方差、風險平價） |
| `statsmodels` / `scipy` | 事件研究自建（OLS + t 檢定） |
| `scikit-learn` | 因子驗證（Phase 7+ 再啟用） |
| `pyarrow` | Parquet 快取讀寫 |
| `apscheduler` | 定時排程（每週五收盤後） |
| `python-telegram-bot` | 推播通知 |
| `plotly` | K 線圖 + 指標疊加 |
| `pytrends` | Google Trends 熱度訊號 |

---

## 台股速查

| 概念 | 要點 |
|------|------|
| 三大法人 | 外資 / 投信 / 自營商；外資最重，外資賣超 + USD 走強是警訊 |
| 融資 | 借錢買股（看多散戶）；餘額高 = 過熱，反向指標 |
| 融券 | 借股做空；回補時推升股價 |
| 月營收 | 每月 10 日前公布，最即時基本面；YoY > 10% 代表成長動能強 |
| 漲跌停 | ±10%；回測注意無法保證以目標價成交 |
| 手續費 | 買賣各 0.1425%；賣出加 0.3% 證交稅（ETF 0.1%）；回測 commission = 0.001425 |
| 交易單位 | 1 張 = 1000 股；回測一般以整張計 |
| 財報週期 | Q1 3月、Q2 8月、Q3 11月、Q4/年報 隔年3月 |

---

## 重要決策

| 決策 | 原因 |
|------|------|
| 不用 FinLab | 付費，要完全自控 |
| 推播用 Telegram Bot | `python-telegram-bot` |
| PTT 情緒分析用 pytrends | Google Trends 已足夠，不跑本地 NLP 模型 |
| 事件研究自建 | PyPI 無現成台股套件；`statsmodels` + `scipy.stats` 約 100 行 |
| TA-Lib 從 source 編譯 | apt 未收錄；`make` 單執行緒，不加 `-j` |
| 籌碼面用 FinMind | TWSE 官方 API 格式散，FinMind 整合好 |
| Dashboard 用 Next.js + FastAPI | 目標使用者是一般大眾，需支援手機、有視覺公信力；Streamlit 不符合 |
| 前端部署 Vercel，後端 Railway | 免費 tier 足夠；Next.js 在 Vercel 一鍵部署 |
| 建皮期間 API 用 Next.js Route Handler 呼叫 python3 subprocess | 省去 FastAPI 複雜度；Phase 9 再遷移 |
| shadcn 4.12 底層是 @base-ui/react（非 Radix UI） | ToggleGroup API 不同：value 是 string[]、active 用 aria-pressed:、無 type="single" |
