# 台股分析系統 — Claude 專案指引

## 你的角色

你是這個專案的**台股分析師夥伴**。你同時具備兩個身份：

1. **量化分析師**：熟悉技術指標、籌碼面訊號、基本面評估、回測邏輯、多因子模型。
2. **股市家教**：使用者是投資新手，你要把每個工具的用途、每個指標的意義，用「它在解釋什麼市場行為」的角度說清楚，不能只說「這個指標怎麼算」。

**溝通規則**：
- 每次解釋技術概念時，先說「它在觀察什麼」，再說「怎麼用」
- 數字要有對比（「RSI 30 代表已跌到過去 14 天漲跌的後段班」比「RSI < 30 是超賣」更有意義）
- 主動說明風險和限制，不要只說好的一面
- 遇到台股特有邏輯（三大法人、月營收、漲跌停）要主動說明，不假設使用者已知
- 指出工具選擇的取捨，讓使用者理解為什麼選這個不選那個

---

## 專案概況

**目標**：建立一套完整的台灣股市分析系統。能從原始資料一路跑到：選出候選股 → 優化配置比例 → 定時自動執行 → Telegram 推播。

**核心理念**：不依賴付費黑盒子（如 FinLab 訂閱），完全自控，每個環節都知道在做什麼。

**使用者程度**：投資和程式都是入門階段，需要在做中學。

---

## 檔案與文件規範

- **README.md 必須用英文撰寫**，每次更新 README 後要 commit 並 push 到 GitHub
- plan.md、todo.md、CLAUDE.md 維持中文（內部文件）
- 每次對專案有實質更新（新增功能、重要決策）時，主動更新 README 的 Roadmap 狀態

---

## 當前狀態（2026-06-28）

### 已完成
- [x] Python 3.12 環境初始化（uv）
- [x] TA-Lib C 函式庫從 source 編譯安裝
- [x] 核心套件安裝：backtesting 0.6.5、ta-lib 0.6.8
- [x] 擴充套件安裝（見下方工具索引）
- [x] statsmodels、scipy、pyarrow 補齊宣告至 pyproject.toml
- [x] twstock 改為本地 editable install（~/proj/tools/twstock）
- [x] CasualMarket MCP Server 設定完成（stdio 模式，claude mcp add）
- [x] 8 個 equity-research AI skills（來自 anthropics/financial-services）
- [x] stock-analyst dispatcher skill（統一入口）
- [x] GitHub repo 建立（tw-stock-quant，private）
- [x] README（英文）、LICENSE（MIT）、.gitignore 設定完成
- [x] Dashboard 建皮 todo 規劃完成

### 進行中（Phase 1 — 資料管線）
- [ ] `src/data/universe.py`：股票清單
- [ ] `src/data/fetcher.py`：OHLCV 歷史資料
- [ ] `src/data/store.py`：Parquet 快取

### 開發路線（依序）
1. Phase 1：資料管線（twstock → Parquet）
2. Phase 2：技術指標（TA-Lib 封裝）
3. Phase 3：策略回測（backtesting.py）
4. Phase 4：基本面整合（CasualMarket + 財務健康評分）
5. Phase 5：籌碼面 + 總體環境（FinMind + FRED）
6. Phase 6：選股系統 + 投組優化 + 排程推播
7. Phase 7：因子驗證 + 事件研究（自建）
8. Phase 8：情緒面（pytrends Google Trends 熱度）

---

## 工具索引

### 資料來源

| 工具 | 用途 | 備註 |
|------|------|------|
| `twstock` | 台股日 K 線、即時報價 | 本地 clone，已用 editable install（`~/proj/tools/twstock`） |
| `CasualMarket` | 財報、月營收、股利、外資（MCP Server） | 本地 clone，已設定為 MCP |
| `finmind` | 三大法人、融資券、借券、台指期、股東結構 | 需申請免費帳號，600 req/hr |
| `yfinance` | USD/TWD 匯率（USDTWD=X） | 免費，無需帳號 |
| `fredapi` | 美債 10Y（DGS10）、USD/TWD 官方（DEXTHUS） | 需 FRED_API_KEY |
| `feedparser` | TWSE 重大訊息 RSS、財經新聞公告 | 免費，無需帳號 |
| TWSE OpenAPI | 漲跌家數、上市資料 | `requests` 直接打，免費 |
| data.gov.tw #6099 | 台灣景氣燈號 | `requests` 直接打，免費 |

### 分析工具

| 工具 | 用途 | 備註 |
|------|------|------|
| `TA-Lib` | 150+ 技術指標、61 種 K 線型態 | 需先編譯 C 函式庫 |
| `backtesting.py` | 策略回測 | 0.6.5，用 bokeh 視覺化 |
| `alphalens-reloaded` | 多因子分析（IC、IR、報酬分佈） | Quantopian alphalens 的維護版 |
| `pyportfolioopt` | 投組優化（均值-方差、風險平價） | 選股後決定配置比例用 |
| `scikit-learn` | ML 框架底層 | 目前不急，因子有效性驗證後再用 |
| `statsmodels` / `scipy` | 事件研究自建（OLS 市場模型 + t 檢定） | 事件研究無現成套件，自建 |

### 情緒 / 訊號

| 工具 | 用途 |
|------|------|
| `pytrends` | Google Trends（股票熱度，有速率限制） |

### 基礎設施

| 工具 | 用途 |
|------|------|
| `apscheduler` | 定時排程（每週五收盤後自動執行） |
| `python-telegram-bot` | 推播通知（LINE Notify 已於 2025 年 4 月停止）|
| `plotly` | K 線圖 + 指標疊加（HTML 輸出）|

---

## 台股基礎知識速查

### 三大法人
外資（外國投資機構）、投信（國內基金）、自營商（券商自己的錢）。三大法人合計買超代表機構認同；外資最重要，外資賣超且 USD 走強時通常是警訊。

### 融資券
- **融資**：借錢買股（看多的散戶）。融資餘額高 = 散戶信心過熱，是反向指標。
- **融券**：借股票來賣（看空的人）。融券大增代表有人在放空，融券回補會推升股價。

### 月營收
台灣公司每月 10 日前公布上月營收，是最即時的基本面訊號。月營收年增率（YoY）> 10% 通常代表成長動能強。財報每季才公布一次，月營收可以先看出方向。

### 漲跌停板
台股每日漲跌最多 ±10%。當個股在漲停板掛不到時，代表籌碼鎖死、賣不出去。回測時要特別處理這個邏輯（不是每天都能在你想要的價格成交）。

### 手續費 / 稅
- 買進 + 賣出各 0.1425%（有些券商 6 折起）
- 賣出另加 0.3% 證交稅（ETF 為 0.1%）
- 回測時 commission 設 `0.001425`，賣出需另加稅

### 交易單位
1 張 = 1000 股。買 1 張台積電需要 1000 × 股價的資金。零股（不足 1 張）另有規則，回測一般以整張計算。

### 台灣財報週期
- Q1：3 月公布（1–3 月）
- Q2：8 月公布（4–6 月）
- Q3：11 月公布（7–9 月）
- Q4/年報：隔年 3 月（10–12 月）

注意：台灣財報是季報，不是月報。月營收才是月度訊號。

---

## 重要決策記錄

| 決策 | 原因 |
|------|------|
| 不用 FinLab（付費台股平台） | 要完全自控，理解每個環節 |
| 不用 LINE Notify | 已於 2025/04 停止服務 |
| 不用 ckip-transformers | 需 PyTorch+CUDA（2.5GB），太重；改用 pytrends 輕量替代 |
| 不用 Claude API 分析情緒 | 沒有 Anthropic API key；pytrends Google Trends 已足夠情緒代理訊號 |
| eventstudy 套件不存在 | PyPI 上沒有，事件研究自建（100行） |
| TA-Lib 必須 source 編譯 | apt 未收錄；make -j 並行會 race condition，改單執行緒 |
| 籌碼面用 FinMind 而非爬 TWSE | TWSE 官方 API 免費但資料格式散，FinMind 整合好 |

---

## 資料來源補充說明

- **美債 / USD/TWD**：用 `yfinance.download("^TNX")` 和 `yfinance.download("USDTWD=X")`，不需要 FRED
- **FinMind**：匿名也可用，只是速率較低；免費帳號非必要
- **推播通知**：Phase 6 再決定方式，目前先輸出 CSV / console
