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

---

## 當前狀態（2026-06-28）

### 已完成
- [x] Python 3.12 + uv、TA-Lib C 函式庫、所有套件
- [x] twstock 本地 editable install（`~/proj/tools/twstock`）
- [x] CasualMarket MCP Server（stdio 模式，`claude mcp add`）
- [x] 8 個 equity-research AI skills + stock-analyst dispatcher
- [x] GitHub repo、README、LICENSE、.gitignore

### 進行中（Phase 1）
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
| 不用 LINE Notify | 2025/04 停止服務 |
| 不用 Claude API / ckip-transformers 做情緒 | 無 Anthropic API key；PyTorch+CUDA 太重；pytrends 已足夠 |
| eventstudy 套件不用 | PyPI 上沒有，自建 100 行 |
| TA-Lib source 編譯 | apt 未收錄；`make -j` 有 race condition，改單執行緒 |
| 籌碼面用 FinMind | TWSE 官方 API 格式散，FinMind 整合好 |
