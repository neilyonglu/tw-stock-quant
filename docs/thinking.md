# 台灣股市分析專案 — 構思過程

這份文件記錄專案從無到有的思考脈絡、決策原因、以及每個選擇背後的取捨。不是技術文件，是決策日誌。

---

## 2026-06-27 — 專案啟動

### 一、工具鏈的確立

**起點**：四個工具已在盤點清單裡，但沒有評估過它們合起來夠不夠用。

| 工具 | 角色 |
|------|------|
| twstock | 歷史 K 線、即時報價（台股專用） |
| CasualMarket | 財報、股利、月營收、外資、ESG（MCP Server） |
| TA-Lib | 技術指標計算 + 61 種 K 線型態識別 |
| backtesting.py | 策略回測框架 |

**評估結論**：四個工具合起來覆蓋了「資料 → 指標 → 策略 → 驗證」的完整流程，對台股個人投資者的分析需求已經足夠。

**明確的缺口**：
- 視覺化（plotly 還沒裝）
- 籌碼面深度（融資券、主力進出）視 CasualMarket 涵蓋範圍而定
- 消息面 / 新聞情緒完全缺失，純量化
- 沒有券商 API，不能下實單

**結論**：如果目標是學習、回測策略、系統化選股，這四個工具已夠用。實單輔助則另需券商 API。

---

### 二、套件安裝

**backtesting.py**：無系統依賴，直接 `uv add backtesting`。

**TA-Lib 的複雜性**：

這是本次安裝最值得記錄的決策點。PyPI 上的 `TA-Lib` 是 C 函式庫的 Python wrapper，不是純 Python 套件。apt 套件庫沒有收錄，所以必須從 source 編譯。

流程：
1. 下載 ta-lib-0.4.0-src.tar.gz（SourceForge）
2. `./configure --prefix=/usr && make && sudo make install && sudo ldconfig`
3. 才能 `uv add TA-Lib`

**踩到的坑**：第一次用 `make -j$(nproc)` 平行編譯失敗（race condition），改成單執行緒 `make` 就正常了。

**專案初始化**：
```bash
uv init --python 3.12   # 系統是 Python 3.13，但指定 3.12 以符合 plan.md
uv add backtesting TA-Lib
```

結果：backtesting 0.6.5、ta-lib 0.6.8，連帶裝好 pandas、numpy 等依賴。

---

### 三、引入 AI Skills 層

**動機**：四個工具解決了「數據處理」，但分析判斷的部分（財報解讀、選股框架、投資論點追蹤）沒有結構化的方法。

**資源來源**：Anthropic 官方釋出了 `anthropics/financial-services` 這個 repo，包含金融服務業的 Claude plugin 與 skill 範本。

**完整盤點**：對 repo 裡 65 個 skill 逐一讀完，依相關性分類。

**篩選標準**：
- 直接對應台股分析流程的需求
- 不依賴付費資料訂閱（排除 LSEG、S&P Global partner skills）
- 不屬於機構業務流程（排除 IB、PE、fund admin、KYC）

**最終選入的 8 個 skills**（均來自 `equity-research` vertical）：

| Skill | 用途 | 對應專案哪個階段 |
|-------|------|----------------|
| `idea-generation` | 系統化選股篩選框架 | Phase 5 選股系統 |
| `earnings-analysis` | 財報公布後快速分析 | Phase 4 基本面整合 |
| `earnings-preview` | 財報公布前設情境 | Phase 4 |
| `thesis-tracker` | 追蹤投資論點 | 貫穿全專案 |
| `catalyst-calendar` | 追蹤催化劑（財報日、除息、法說會） | Phase 5 |
| `morning-note` | 每日市場摘要 | Phase 6 報告 |
| `model-update` | 新財報出來後更新估值 | Phase 4 |
| `sector-overview` | 選股前的產業大環境分析 | Phase 5 前置 |

**排除但值得注意的**：
- `skill-creator`：教你建自己的 skill，未來可以用來做「台股專屬 skill」（twstock-fetcher、taifex-screener 等）
- `comps-analysis`、`dcf-model`：有用但需要付費資料源，暫不引入

**存放位置**：`.claude/skills/<skill-name>/SKILL.md`

`earnings-analysis` 因為原始 repo 有附 references 子目錄（workflow、report-structure、best-practices），一併複製進來。

---

### 四、建立 Dispatcher（主控 Skill）

**問題**：8 個 skill 各有各的觸發條件，使用者不熟悉的話不知道什麼情況要用哪個。

**解法**：建立一個 `stock-analyst` dispatcher skill，作為所有分析請求的統一入口。

**設計思路**：
- 用一張路由表對應「使用者意圖 → 對應 skill」
- 每次執行前先告訴使用者「我判斷你要做 X，所以我要用 skill Y」，讓使用者能理解決策過程
- 針對模糊需求，最多問一個問題澄清，不多問
- 內建台股專有知識（財報週期、月營收時間點、法說會慣例）

**存放位置**：`.claude/skills/stock-analyst/SKILL.md`

**路由邏輯**（簡化）：

```
財報後分析  →  earnings-analysis
財報前準備  →  earnings-preview
找新標的    →  idea-generation
追蹤持倉    →  thesis-tracker
找事件日期  →  catalyst-calendar
每日摘要    →  morning-note
更新數字    →  model-update
了解產業    →  sector-overview
```

---

## 目前狀態（2026-06-27 EOD）

**已完成**：
- [x] 專案初始化（uv + pyproject.toml）
- [x] TA-Lib C 函式庫編譯安裝
- [x] backtesting.py + TA-Lib Python 套件安裝
- [x] 8 個 equity-research skills 加入 `.claude/skills/`
- [x] stock-analyst dispatcher 建立

**待完成（Phase 1 起點）**：
- [ ] 安裝其他依賴（plotly、pyarrow、pytest、jupyter、twstock）
- [ ] `src/data/universe.py`：維護股票清單
- [ ] `src/data/fetcher.py`：用 twstock 抓 OHLCV
- [ ] `src/data/store.py`：Parquet 快取層
- [ ] 驗收：能抓到 2330 的歷史資料並存成 Parquet

---

## 尚未解決的問題

1. **CasualMarket MCP 的覆蓋範圍**：融資券、主力進出是否有涵蓋？籌碼面分析的深度有待確認。
2. **台股 skills 的本土化**：目前引入的 skills 都是英文框架，財報格式（台灣 IFRS vs. 美國 GAAP）、指標定義（月營收年增率 vs. quarterly revenue）需要在使用時手動說明差異。未來可以用 `skill-creator` 建立台股專屬版本。
3. **資料更新頻率**：twstock 的 rate limit（每 5 秒 3 個 request）在批次下載全市場時會是瓶頸，需要在 fetcher 加 sleep 機制。

---

## 2026-06-27 — 缺口分析與工具擴充

### 五、系統性缺口盤點

初始四個工具覆蓋了「技術面分析 + 基本面資料 + 回測」，但對一個完整的台股分析系統，缺少以下幾個維度：

| 缺口 | 重要性 | 說明 |
|------|--------|------|
| 籌碼面（三大法人、融資券、借券） | 🔴 高 | 台股籌碼訊號是主流投資人必看指標 |
| 總體經濟（景氣燈號、USD/TWD、美債）| 🔴 高 | 台灣是出口導向經濟，匯率與外資行為高度相關 |
| 財務健康評分（Piotroski、Altman Z）| 🟡 中 | 基本面篩選的量化底線，目前只有原始財報數字 |
| 多因子框架（價值/動能/品質）| 🟡 中 | 學術實證最充分的選股方法，目前 scorer.py 尚無依據 |
| 市場廣度（漲跌家數）| 🟡 中 | 判斷多頭是否有廣度，純看個股容易忽略市場結構 |
| 情緒/消息面 | 🟢 低 | Google Trends、PTT 情緒，屬於輔助訊號 |
| 事件研究 | 🟢 低 | 量化法說會、除息等事件的前後報酬效應 |
| 排程/推播 | 🟢 低 | 自動化執行與通知，是最後才需要的基礎設施 |

**為何 USD/TWD 特別重要**：台積電、聯發科等大型股收入以美元計價，USD/TWD 每動 1 元，台積電季 EPS 差約 0.3–0.5 元。匯率不進模型，估值就是錯的。此外，USD 走強時外資傾向撤出新興市場，台股外資賣超與 USD 強升高度相關。

---

### 六、工具研究結果

針對五個缺口方向各做了工具調查，以下是結論。

#### 籌碼面

**FinMind** 是最佳選擇，單一套件覆蓋所有需求：

| 資料 | 資料集名稱 |
|------|-----------|
| 三大法人買賣超 | `TaiwanStockInstitutionalInvestorsBuySell` |
| 融資融券餘額 | `TaiwanStockMarginPurchaseShortSale` |
| 借券賣出 | `TaiwanStockSecuritiesLending` |
| 股東結構 | `TaiwanStockShareholding` |

免費版 600 req/hr（需免費帳號），單次限查一支股票；批次下載需付費。補充 TWSE/TPEX 官方 OpenAPI（完全免費，無需帳號，`requests` 直接打）。

#### 總體經濟

| 資料 | 工具 | 費用 |
|------|------|------|
| 景氣燈號 | data.gov.tw dataset #6099（`requests`）| 免費 |
| USD/TWD | `yfinance` ticker `USDTWD=X` | 免費 |
| USD/TWD 官方 | FRED `DEXTHUS` via `fredapi` | 免費（需申請 key）|
| 美債 10Y | FRED `DGS10` via `fredapi` | 免費（需申請 key）|
| 台灣 PMI | **無好的免費方案** | Trading Economics/S&P 皆付費 |
| 市場廣度 | TWSE OpenAPI | 免費 |

PMI 目前決定暫時跳過，等有付費需求時再考慮。

#### 財務健康評分

PyPI 上沒有現成的台股適用套件。結論是：資料來源用 CasualMarket（已有），計算邏輯自建。Piotroski F-score（9 個財報指標 0/1 計分）和 FCF 轉換率邏輯不複雜，可以作為 `src/indicators/health.py` 實作。

#### 多因子框架

- **`alphalens-reloaded`**：Quantopian 原版的維護 fork，用來分析因子的報酬率、IC、IR，是最成熟的免費工具。
- **`filib`**：有計算因子的框架，但 alpha 版，適合參考而非生產使用。

#### 情緒/消息面

- **`pytrends`**：Google Trends 非官方 wrapper，有速率限制問題，需要代理伺服器做批次查詢。
- **`ptt-crawler`**：PTT Stock 版爬蟲，有維護斷更風險。
- **`ckip-transformers`**：台大 CKIP 繁體中文 NLP，可接在爬蟲後做情緒分析。

#### 排程與推播

- **`APScheduler`**：成熟的 Python job scheduler，支援 cron 語法，免費。
- **⚠️ LINE Notify 已於 2025 年 4 月停止服務**，不能用。改用 **`python-telegram-bot`**（Telegram Bot API），設定同樣簡單，長期維護更穩定。

#### 事件研究

- **`eventstudy`（PyPI 不存在，已確認）**：研究時誤判，PyPI 上沒有這個套件。
- **改為自建**：事件研究邏輯不複雜，用 `statsmodels`（市場模型 OLS 估算預期報酬）+ `scipy.stats`（t 檢定）即可。`statsmodels` 已是 `alphalens-reloaded` 的依賴，環境中已有。實作約 100 行 Python，放在 `src/events/study.py`。

#### 補充缺口工具

缺口分析後追加的三個工具：

- **`pyportfolioopt`**：投組優化（均值-方差、Black-Litterman、風險平價），解決「選出 20 支股票後如何分配比例」的問題。
- **`feedparser`**：解析 RSS feed，用於抓取 TWSE 重大訊息和鉅亨網財經新聞，覆蓋即時公告監控缺口。
- **`scikit-learn`**：ML 基礎套件，作為未來因子非線性建模的底層工具。目前不急，但先裝好。

#### ckip-transformers（已移除）

`ckip-transformers` 是台大 CKIP 的繁體中文 NLP 工具，原本計畫用來分析 PTT 文章情緒。但安裝時帶入了 PyTorch + NVIDIA CUDA（合計約 2.5 GB），對多數個人電腦來說太重，且 Phase 8 是最低優先度的功能。

**決策**：移除。PTT 情緒分析改為將爬蟲抓到的文章直接送 Claude API 做情緒判斷，不在本地跑模型。這樣更輕量、更準確，而且專案本身就在用 Claude。

---

## 目前狀態（2026-06-27 更新）

**已完成**：
- [x] 專案初始化（uv + pyproject.toml，Python 3.12）
- [x] TA-Lib C 函式庫從 source 編譯安裝
- [x] 核心套件：backtesting 0.6.5、ta-lib 0.6.8
- [x] 擴充套件：finmind 2.0.4、yfinance 1.4.1、fredapi 0.5.2、alphalens-reloaded 0.4.6、apscheduler 3.11.2、python-telegram-bot 22.8、pytrends 4.9.2、pyportfolioopt 1.6.0、feedparser 6.0.12、scikit-learn 1.9.0
- [x] 輔助套件：twstock 1.5.1、plotly 6.8.0、pytest 9.1.1、jupyter 1.1.1
- [x] ckip-transformers 移除（PyTorch 太重，改用 Claude API）
- [x] 8 個 equity-research skills 加入 `.claude/skills/`
- [x] stock-analyst dispatcher 建立（`.claude/skills/stock-analyst/`）
- [x] 缺口分析完成，工具選型確定
- [x] `CLAUDE.md` 建立（persona + 專案 context，每次新 session 自動載入）
- [x] `.env.example` 建立（API key 清單）

**待完成（Phase 1 起點）**：
- [ ] 建立 `src/` 和 `data/` 目錄結構
- [ ] `src/data/universe.py`：股票清單（上市 + 上櫃）
- [ ] `src/data/fetcher.py`：用 twstock 抓 OHLCV
- [ ] `src/data/store.py`：Parquet 快取層
- [ ] 驗收：`python -m src.data.fetcher 2330` 能產出 Parquet

**已知待決策**：
- CasualMarket MCP 的籌碼面覆蓋範圍（是否與 FinMind 重疊，避免重複開發）
- 台灣 PMI 暫不引入，等有付費資料需求時再評估
