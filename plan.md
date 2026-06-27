# 台灣股市分析專案計畫

## 專案目標

建立一套完整的台灣股市分析系統，從資料抓取、技術指標計算、策略回測，到基本面整合與選股輸出。
採用漸進式開發，每個 Phase 都能獨立運作、產出有意義的結果。

**最終目標**：系統定期掃全市場，輸出「可以買哪檔股票、在什麼時機買賣」的可操作建議。

---

## 投資決策框架（系統大腦）

這是整個系統的核心邏輯——每一個 Phase 都在為這個框架的某一層提供材料。

### 四層篩選架構（由外到內）

```
第一層：總體環境過濾
    ↓（大環境不對，全面縮手）
第二層：基本面初篩
    ↓（財務有問題的，直接排除）
第三層：籌碼面確認
    ↓（沒有法人撐腰，跳過）
第四層：技術面擇時
    ↓（選對股，還要選對時機進出）
輸出：買賣訊號 + 配置比例
```

---

### 第一層：總體環境 — 現在適合操作嗎？

**觀察的是**：整個市場的水溫，判斷要積極還是保守。

| 指標 | 觀察什麼 | 影響 |
|------|----------|------|
| 景氣燈號（國發會） | 紅燈=過熱、藍燈=衰退、綠燈=正常 | 藍燈區間降低持股比例 |
| 美債 10Y 殖利率 | 快速走升代表資金成本增加 | 成長股估值承壓，減少高本益比標的 |
| USD/TWD 匯率 | 外資匯率收益影響進出意願 | 台幣大幅貶值時，外資容易撤出 |
| 市場廣度（漲跌家數） | 多數股票在漲 vs 只有少數在漲 | 廣度萎縮是行情末段警訊 |

**判斷結果**：
- **多頭環境**（景氣綠燈以上、美債穩定）→ 滿倉操作，積極找標的
- **盤整環境**（訊號混雜）→ 半倉，只選最強的股
- **空頭環境**（景氣藍燈、外資大賣）→ 縮手，以現金為主

---

### 第二層：基本面初篩 — 這家公司值得研究嗎？

**觀察的是**：公司的獲利能力和財務健全度，排除地雷股。

**硬性門檻（不符合就排除）**：
- ROE（股東權益報酬率）> 12%：公司幫股東賺錢的效率
- 近 4 季 EPS 均為正值：不虧錢
- 月營收近 3 個月 YoY（年增率）> 0%：業績還在成長方向
- Piotroski F-score ≥ 6（0–9 分）：財務健康度基本合格

**加分項（提高排名用）**：
- 月營收 YoY > 10%：成長動能強
- FCF 轉換率 > 80%：獲利是真實現金，不是帳面數字
- 殖利率 > 4%：有具體回饋股東
- Altman Z-score > 2.99：破產風險低

---

### 第三層：籌碼面確認 — 有大戶在買嗎？

**觀察的是**：外資、投信、自營商的行為，因為大機構的資金量能推動股價。

**訊號解讀**：

| 籌碼訊號 | 意義 | 操作含義 |
|----------|------|----------|
| 外資連續買超 5 日以上 | 外資認同這檔股票 | 加分，可以跟進 |
| 投信連續買超（月底前） | 基金在建倉 | 加分，特別是季報前 |
| 外資 + 投信同步買 | 法人齊買，力道強 | 強力加分 |
| 融資餘額大幅攀升 | 散戶借錢追高，風險增加 | 減分，小心反轉 |
| 融券大增 | 有人在放空 | 需注意，但回補也會拉升 |

**排除條件**：融資餘額佔流通股本 > 5%（過度散戶化，籌碼不穩定）

---

### 第四層：技術面擇時 — 什麼時候進？什麼時候出？

**觀察的是**：股價走勢和成交量，選對股還要找對時機，避免「對的股票、錯的時間點」。

#### 買進訊號（需多個條件同時符合）

**趨勢確認**（必要條件）：
- 股價站上 20 日均線，且 20MA > 60MA（中期趨勢向上）
- MACD 在零軸以上，或 MACD 金叉剛形成

**動能確認**（至少一個）：
- RSI 在 40–70 之間（不超買也不超弱）
- KD 金叉，且 K 值 < 80（還有上漲空間）

**量能確認**（必要條件）：
- 突破時成交量 > 5 日均量 1.5 倍（放量突破才算數）

**K 線型態加分**（選配）：
- 晨星、錘子線、吞噬型態（TA-Lib 61 種型態）

#### 賣出訊號（觸發任一條件）

**止損出場**（保護本金，優先）：
- 買進後股價跌破進場價 7%（固定停損）
- 跌破 20 日均線且放量（趨勢破壞）
- ATR 停損：進場價 - 2×ATR（依波動度調整）

**獲利出場**（鎖定利潤）：
- RSI > 75 且開始回頭（超買區反轉）
- MACD 死叉且放量（動能轉弱）
- 基本面惡化：月營收連續 3 個月 YoY 轉負

---

### 輸出格式

每週五收盤後，系統產出：

```
== 本週選股推薦（2026-07-05） ==

總體環境：多頭 ✅
推薦操作強度：積極

| 排名 | 股票 | 買進理由（三層）| 建議進場區間 | 停損 | 配置比例 |
|------|------|----------------|-------------|------|----------|
| 1 | 2330 台積電 | 法人連買 7 日 / RSI 52 / MACD 金叉 | 900–920 | 860 | 20% |
| 2 | 2454 聯發科 | 月營收 YoY+18% / 外投同買 / 突破 MA60 | 1100–1130 | 1020 | 15% |
...

風險提示：本清單僅為參考，不構成投資建議。
```

---

## 研究步驟（依序執行）

### Step 1：先搞懂「什麼樣的股票值得研究」

在開始寫程式之前，先建立對台股的基本認識：

1. **看台積電（2330）作為基準**：台積電是台股最大的股票，用它來理解每個指標的「正常值」
2. **理解三大法人報告**：每天看 TWSE 公布的三大法人買賣超，感受數字的規模
3. **讀一份財報**：找台積電最新一季財報，理解 EPS / ROE / 現金流是從哪裡來的

**這步不用寫程式，用眼睛看，建立直覺。**

---

### Step 2：資料管線（Phase 1）

**先能穩定拿到資料，才能做任何分析。**

沒有資料，一切都是空談。這步的重點是：
- 能抓到任意股票的歷史 K 線
- 資料存起來，下次不用重抓
- 財務資料也能拉到

完成後驗證：`python -m src.data.fetcher 2330` 跑出來有 OHLCV 資料。

---

### Step 3：技術指標（Phase 2）

**加上「分析用的尺」。**

光有 K 線看不出什麼，要加上指標才能量化趨勢和動能：
- MA / EMA：看趨勢方向
- MACD：看動能轉折
- RSI：看是否超買超賣
- Bollinger Bands：看波動區間

完成後驗證：跑一支股票的指標圖，能看到 MACD 金叉 / RSI 超賣的歷史時點。

---

### Step 4：策略回測（Phase 3）

**用歷史資料檢驗「如果當時這樣操作，結果如何」。**

這步非常重要——你的直覺會說某個訊號有效，回測告訴你實際勝率是多少。

目標：對台積電跑 2020–2025 年回測
- 勝率多少？
- 最大回撤多少？（跌最深的時候）
- Sharpe 比率多少？（報酬除以波動）

**注意**：回測結果好不代表未來一定好（過擬合），但回測結果差代表策略本身有問題。

---

### Step 5：基本面整合（Phase 4）

**篩掉財務有問題的公司。**

技術面可能讓你進到一個「線型漂亮但公司快倒閉」的股票，加入基本面篩選是保護機制。

- Piotroski F-score：九個財報問題，每個符合得 1 分，≥ 6 才考慮
- 月營收 YoY：最即時的業績訊號，每月 10 日更新

---

### Step 6：籌碼面分析（Phase 5）

**確認有大戶同行。**

散戶的判斷常常是情緒化的；機構法人的買賣有研究支撐，跟著法人的方向有更高的勝算。

外資連續買超 + 投信同步進場，是台股最有效的籌碼訊號之一。

---

### Step 7：整合選股 + 投組優化（Phase 6）

**把以上四層整合成一個數字，再決定配置比例。**

四層分別給分，加權後排名。排名前 20% 的股票，再用 PyPortfolioOpt 決定每檔配置多少比例（不讓單一股票佔太多）。

---

### Step 8：驗證因子有效性（Phase 7）

**確認你選的指標在台股真的有效，而不是你「以為」有效。**

用 Alphalens 計算 IC（Information Coefficient）：
- IC > 0.05 代表因子有一定預測力
- IC < 0 代表因子是反向的（或者根本沒效）

這步會讓你發現某些「直覺上很合理」的指標，在台股實際上沒用。

---

### Step 9：自動化 + 推播（Phase 6 後段）

**每週自動跑，不用手動觸發。**

- 每週五 13:30 收盤後自動掃全市場
- Telegram 推播本週前 20 候選股 + 配置建議
- 自動監控持倉的重大公告（TWSE RSS）

---

## 現有工具盤點

### 核心工具（已安裝）

| 工具 | 位置 | 狀態 | 用途 |
|------|------|------|------|
| `twstock` | `~/proj/tools/twstock` | ✅ 活躍（2026-04 更新） | 抓 TWSE/TPEX 歷史 K 線、即時報價 |
| `CasualMarket` | `~/proj/tools/CasualMarket` | ✅ 本地 MCP | 財務報表、股利、營收、外資、ETF |
| `TA-Lib` | PyPI（已安裝） | ✅ 業界標準 | 150+ 技術指標、61 種 K 線型態 |
| `backtesting.py` | PyPI（已安裝） | ✅ 仍維護，適合入門 | 策略回測（快速原型用） |

### 擴充工具（已安裝）

| 工具 | 狀態 | 用途 | 費用 |
|------|------|------|------|
| `finmind` | ✅ 活躍，持續更新 | 三大法人、融資融券、借券、台指期 | 免費 600 req/hr（需申請帳號）|
| `yfinance` | ✅ 活躍 | USD/TWD 匯率、美股補充 | 免費 |
| `fredapi` | ✅ 活躍 | 美債殖利率（DGS10） | 免費（需 FRED_API_KEY）|
| `alphalens-reloaded` | ✅ 活躍（2025-06 更新） | 多因子分析（IC、IR） | 免費 |
| `pyportfolioopt` | ✅ 活躍（2026-02 更新） | 投組優化（均值-方差、HRP） | 免費 |
| `apscheduler` | ✅ 活躍 | 定時排程 | 免費 |
| `python-telegram-bot` | ✅ 活躍 | 推播通知 | 免費 |
| `pytrends` | ⚠️ 速率限制嚴格 | Google Trends 熱度（輔助用） | 免費 |
| `feedparser` | ✅ 活躍 | TWSE 公告 RSS 解析 | 免費 |
| `scikit-learn` | ✅ 業界標準 | ML 底層（Phase 7 後才用） | 免費 |

### 即時報價替代方案（免申請、免費）

| 工具 | 用途 | 備註 |
|------|------|------|
| `twstock.realtime` | 單股即時報價 | 直接抓 TWSE，不需帳號 |
| TWSE OpenAPI `/v1/exchangeReport/STOCK_DAY_ALL` | 當日全市場行情（一次全拿） | requests 直打，完全免費 |
| `yfinance` | 分鐘線（有 15 分延遲） | 不需帳號，夠用於 Dashboard 顯示 |

> **Fugle（選配）**：如果未來想要官方即時盤中資料或分鐘線，可申請 [developer.fugle.tw](https://developer.fugle.tw/) 免費帳號，安裝 `fugle-marketdata`。但不是必要，上面三個替代方案已能滿足所有需求。

> **注意 1**：`eventstudy` 套件 PyPI 上不存在，事件研究改為用 `statsmodels` + `scipy.stats` 自建（約 100 行，放 `src/events/study.py`）。
> **注意 2**：`ckip-transformers`（繁體中文 NLP）已移除——需要 PyTorch + CUDA（約 2.5 GB），佔資源且優先度最低。PTT 情緒分析改為將文章直接送 Claude API 做判斷。

### 免費 API（無需套件）

| 資料源 | 說明 |
|--------|------|
| TWSE OpenAPI `openapi.twse.com.tw` | 上市股票官方資料、漲跌家數 |
| TPEX OpenAPI `tpex.org.tw/openapi` | 上櫃股票官方資料 |
| data.gov.tw dataset #6099 | 台灣景氣燈號（國發會每月公布）|

---

## 技術選型

```
Python 3.12+
uv                    # 套件管理

# 資料處理
pandas                # 資料處理
numpy                 # 數值計算
pyarrow               # Parquet 儲存

# 市場資料
twstock               # 台股歷史 K 線（TWSE/TPEX）
finmind               # 籌碼面資料（三大法人、融資券）
yfinance              # USD/TWD 匯率
fredapi               # 美債殖利率（FRED）

# 技術分析
TA-Lib                # 150+ 技術指標、K 線型態

# 基本面 / 財務健康
CasualMarket          # 財報、股利、月營收（MCP）
# Piotroski F-score、Altman Z-score 自建於 src/indicators/health.py

# 量化分析
backtesting.py        # 策略回測
alphalens-reloaded    # 多因子分析（IC、IR）
pyportfolioopt        # 投組優化（選股後決定配置比例）
scikit-learn          # ML 框架（因子非線性建模）
statsmodels           # 事件研究自建基礎（市場模型 OLS）
scipy                 # 統計檢定（事件研究 t-test）

# 情緒/消息
pytrends              # Google Trends
feedparser            # RSS 解析（TWSE 公告、財經新聞）
# PTT 情緒分析改為直接呼叫 Claude API，不用本地 NLP 模型

# 視覺化 + Dashboard
streamlit             # 互動式 Web Dashboard 框架（2026 仍是最主流的選擇）
streamlit-lightweight-charts  # TradingView 官方 K 線元件（最漂亮的金融圖表）
plotly                # 輔助圖表（法人籌碼折線、投組圓餅圖等非 K 線場景）
# backtesting.py 視覺化：回測結果（bokeh，獨立 HTML）

# 基礎設施
apscheduler           # 定時排程
python-telegram-bot   # 推播通知（LINE Notify 已於 2025 停止）
pytest                # 測試
jupyter               # 探索分析（開發期用，不上 Dashboard）
```

---

## 目錄結構

```
stock_analysis/
├── plan.md
├── docs/
│   └── thinking.md        # 構思過程與決策日誌
├── pyproject.toml
├── .env.example           # FRED_API_KEY, FINMIND_TOKEN, TELEGRAM_BOT_TOKEN
│
├── data/
│   ├── raw/               # 原始資料（Parquet）
│   ├── processed/         # 加完指標後的資料
│   ├── chip/              # 籌碼資料（三大法人、融資券）
│   ├── macro/             # 總體資料（景氣燈號、匯率、美債）
│   └── universe/          # 股票清單（上市、上櫃、ETF）
│
├── src/
│   ├── data/
│   │   ├── fetcher.py         # 歷史 OHLCV（twstock）
│   │   ├── realtime.py        # 即時報價
│   │   ├── fundamental.py     # 財務資料（CasualMarket MCP）
│   │   ├── chip.py            # 籌碼資料（FinMind / TWSE OpenAPI）
│   │   ├── macro.py           # 總體資料（景氣燈號、USD/TWD、美債）
│   │   ├── universe.py        # 股票清單管理
│   │   └── store.py           # Parquet 讀寫快取
│   │
│   ├── indicators/
│   │   ├── trend.py           # 趨勢：MA、EMA、MACD、ADX
│   │   ├── momentum.py        # 動能：RSI、KD、Williams %R
│   │   ├── volatility.py      # 波動：ATR、布林通道
│   │   ├── volume.py          # 量能：OBV、VWAP、量比
│   │   ├── pattern.py         # K 線型態（TA-Lib 61 種）
│   │   └── health.py          # 財務健康評分（Piotroski F-score、Altman Z、FCF 轉換率）
│   │
│   ├── strategies/
│   │   ├── base.py            # 策略基礎類別（台股：整張、漲跌停）
│   │   ├── ma_cross.py        # 均線交叉
│   │   ├── rsi_reversal.py    # RSI 超買超賣
│   │   ├── macd_trend.py      # MACD 趨勢跟隨
│   │   └── fundamental_mom.py # 基本面動能
│   │
│   ├── backtest/
│   │   ├── runner.py          # 回測執行器
│   │   ├── optimizer.py       # 參數最佳化（grid search）
│   │   └── metrics.py         # Sharpe、最大回撤、勝率、盈虧比
│   │
│   ├── screening/
│   │   ├── technical.py       # 技術面篩選（第四層）
│   │   ├── fundamental.py     # 基本面篩選（第二層）
│   │   ├── chip.py            # 籌碼面篩選（第三層）
│   │   └── scorer.py          # 四層加權評分 → 最終排名
│   │
│   ├── macro/
│   │   └── context.py         # 總體環境判斷（第一層：多頭/空頭/盤整）
│   │
│   ├── sentiment/
│   │   ├── trends.py          # Google Trends 搜尋熱度
│   │   └── nlp.py             # PTT 文字情緒分析（Claude API）
│   │
│   ├── events/
│   │   └── study.py           # 事件研究（法說會/除息前後 CAR，自建）
│   │
│   ├── alerts/
│   │   ├── scheduler.py       # 定時排程（APScheduler）
│   │   └── notify.py          # Telegram 推播
│   │
│   └── report/
│       ├── chart.py           # plotly K 線圖 + 指標疊加
│       └── summary.py         # 回測報告 Markdown 輸出
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_indicator_playground.ipynb
│   ├── 03_strategy_development.ipynb
│   ├── 04_screening_demo.ipynb
│   ├── 05_chip_analysis.ipynb
│   └── 06_macro_context.ipynb
│
└── tests/
    ├── test_fetcher.py
    ├── test_indicators.py
    ├── test_strategies.py
    └── test_chip.py
```

---

## 開發計畫（Phase 對應四層框架）

### Phase 1 — 資料管線（第一優先）

**目標**：能穩定抓到資料、快取在本地、不每次都打 API。

- [ ] 初始化 `pyproject.toml`，安裝基礎依賴
- [ ] `src/data/universe.py`：維護一份股票清單（上市 + 上櫃），從 twstock codes 產生
- [ ] `src/data/fetcher.py`：用 twstock 抓指定股票的歷史 OHLCV，支援起始日期
- [ ] `src/data/store.py`：Parquet 快取層，避免重複下載；支援 `update_if_stale(days=1)`
- [ ] `src/data/fundamental.py`：透過 CasualMarket MCP client 拉財務資料（股利、營收、財報）
- [ ] 驗收：`python -m src.data.fetcher 2330 2330 2454` 能產出 `data/raw/` 的 Parquet 檔

**關鍵限制**：
- twstock 對 TWSE 的 rate limit 是每 5 秒 3 個 request，批次下載要加 sleep
- CasualMarket 已有 rate limiting 機制，直接呼叫即可

---

### Phase 2 — 技術指標模組（對應第四層）

**目標**：對任意 OHLCV DataFrame 計算一套標準指標，為技術面擇時做準備。

- [ ] `src/indicators/trend.py`：SMA(5/10/20/60)、EMA、MACD
- [ ] `src/indicators/momentum.py`：RSI(14)、KD(9,3,3)、Williams %R
- [ ] `src/indicators/volatility.py`：ATR、Bollinger Bands(20,2)
- [ ] `src/indicators/volume.py`：OBV、量比（今日量 / 5日均量）
- [ ] `src/indicators/pattern.py`：封裝 TA-Lib 的 61 種 K 線型態，輸出 signal column
- [ ] 統一介面：`add_indicators(df: pd.DataFrame) -> pd.DataFrame`
- [ ] 驗收：jupyter notebook 跑一支股票，能畫出含 MACD、RSI、布林通道的完整圖

---

### Phase 3 — 策略回測（驗證第四層買賣邏輯）

**目標**：能跑至少 3 個策略的回測，輸出績效報告，確認技術面邏輯是否真的有效。

- [ ] `src/strategies/base.py`：繼承 backtesting.py 的 `Strategy`，加上台股特有邏輯（整張 1000 股、漲跌停板）
- [ ] `src/strategies/ma_cross.py`：短期均線上穿長期均線買進，反向賣出
- [ ] `src/strategies/rsi_reversal.py`：RSI < 30 買進，RSI > 70 賣出，加 ATR 停損
- [ ] `src/strategies/macd_trend.py`：MACD 金叉買進，死叉賣出，量能過濾
- [ ] `src/backtest/runner.py`：封裝 `Backtest(data, Strategy, cash=..., commission=0.001425)`
- [ ] `src/backtest/optimizer.py`：對策略參數做 grid search（小心 overfitting）
- [ ] `src/backtest/metrics.py`：年化報酬、Sharpe、最大回撤、勝率、盈虧比
- [ ] 驗收：對台積電 (2330) 跑 2020-2025 回測，能輸出交易紀錄和績效摘要

**注意事項**：
- 手續費：買賣各 0.1425%，賣出另加證交稅 0.3%（ETF 為 0.1%）
- 台股最小單位：1 張 = 1000 股，`exclusive_orders=True`

---

### Phase 4 — 基本面整合（建立第二層篩選）

**目標**：把財務資料整進分析流程，排除地雷股，建立財務健康評分。

- [ ] 接 CasualMarket `/financial/statements` 拉 EPS、ROE、毛利率
- [ ] 接 `/financial/revenue` 拉月營收年增率（MoM / YoY）
- [ ] 接 `/financial/dividend` 拉殖利率、股利連續成長年數
- [ ] `src/indicators/health.py`：
  - Piotroski F-score（9 個財報指標 0/1 計分，總分 0–9）
  - FCF 轉換率（營業現金流 ÷ 淨利，判斷獲利品質）
  - Altman Z-score（破產風險預警）
- [ ] `src/screening/fundamental.py`：定義篩選條件（ROE > 12%、近 4 季 EPS 成長、月營收 YoY > 0%）
- [ ] `src/strategies/fundamental_mom.py`：基本面良好 + 技術面突破的組合策略
- [ ] 驗收：能用基本面條件 + 健康評分從全市場篩出候選清單

---

### Phase 5 — 籌碼面與總體環境（建立第一、三層）

**目標**：把「誰在買」和「大環境對不對」加進選股框架。

- [ ] `src/data/chip.py`：用 FinMind 抓三大法人、融資融券、借券賣出
  - 主要：`TaiwanStockInstitutionalInvestorsBuySell`
  - 補充：`TaiwanStockMarginPurchaseShortSale`
- [ ] `src/data/macro.py`：
  - 景氣燈號（data.gov.tw dataset #6099）
  - USD/TWD 匯率（yfinance `USDTWD=X`）
  - 美債 10Y 殖利率（FRED `DGS10` via fredapi）
  - 市場廣度：漲跌家數（TWSE OpenAPI）
- [ ] `src/macro/context.py`：整合總體指標 → 輸出市場環境分類（多頭/空頭/盤整）
- [ ] `src/screening/chip.py`：籌碼面篩選（法人連續買超 N 日、融資券比率）
- [ ] `src/screening/scorer.py`：整合技術 + 基本面 + 籌碼 + 總體四個維度的多因子評分
- [ ] 驗收：同樣條件的股票，在不同總體環境下的排名會有所不同

---

### Phase 6 — 選股系統、投組優化與排程（產出最終推薦）

**目標**：定期自動掃全市場，輸出可操作的候選清單，並決定配置比例。

- [ ] `src/screening/technical.py`：技術面條件集合（均線排列、RSI 位置、量突破）
- [ ] 批次掃描腳本：每週跑一次，輸出 TOP 20 候選股 CSV + 摘要報告
- [ ] `src/portfolio/optimizer.py`：用 `pyportfolioopt` 對候選股做投組優化
  - 均值-方差最佳化（Sharpe 最大化）
  - 風險平價（Risk Parity）作為保守選項
  - 加入最大持倉限制（單股不超過 20%）
- [ ] `src/alerts/news.py`：用 `feedparser` 監控 TWSE 重大訊息 RSS，過濾持倉相關公告
- [ ] `src/alerts/scheduler.py`：用 APScheduler 設定週期性任務（每週五收盤後自動執行）
- [ ] `src/alerts/notify.py`：用 python-telegram-bot 推播選股結果和投組建議
- [ ] 驗收：腳本一行指令能輸出本週推薦清單 + 建議配置比例，並推播 Telegram

---

### Phase 7 — 因子分析與事件研究

**目標**：用學術工具驗證因子有效性、量化事件效應，確認「我選的指標在台股真的有效」。

- [ ] 用 `alphalens-reloaded` 分析各因子的 IC（Information Coefficient）和報酬分佈
  - 確認哪些因子在台股真的有效
  - 找出因子的最佳持有週期
- [ ] `src/events/study.py`：**自建**事件研究模組（`statsmodels` + `scipy.stats`）
  - 估計期（event window 前 120 日）：用市場模型 OLS 算 alpha/beta
  - 事件窗口（前後各 5 日）：計算 AR = 實際報酬 - 預期報酬
  - 累積 CAR，做 t 檢定確認統計顯著性
  - 案例：法說會前後 CAR、月營收優於預期後的報酬、外資連續買超後的表現
- [ ] 驗收：能輸出「台股外資連續買超 5 日後，10 日平均 CAR = X%（p < 0.05）」這類量化結論

---

### Phase 8 — 情緒面整合（選配）

**目標**：把市場情緒納入選股的輔助訊號。

- [ ] `src/sentiment/trends.py`：用 pytrends 抓股票名稱的 Google 搜尋趨勢（熱度異常上升 = 散戶關注增加）
- [ ] PTT Stock 版情緒分析：爬蟲抓文章 → 直接呼叫 Claude API 做正/負情緒判斷（不用本地 NLP 模型）
- [ ] 將情緒分數加入 scorer.py 作為輔助因子（權重設低，防止雜訊干擾）
- [ ] 驗收：能計算任意股票過去 30 天的 Google 搜尋熱度趨勢

---

### Phase 9 — Dashboard 與視覺化

**目標**：把所有分析結果整合進一個可以即時互動的介面，三個功能都做到。

**工具選擇：Streamlit + streamlit-lightweight-charts**

- **Streamlit**：2026 仍是 Python 做 Dashboard 最主流的工具，社群龐大、模板多
- **streamlit-lightweight-charts**：把 TradingView 的官方 K 線元件包進 Streamlit——你在 TradingView 看到的那種流暢、可縮放、專業 K 線圖，就是這個庫
- 兩個合在一起：框架用 Streamlit（快），K 線用 TradingView 等級元件（漂亮）
- `streamlit run app.py` 一行啟動，本地瀏覽器開啟

---

#### 頁面一：市場總覽（看盤 Dashboard）

**觀察的是**：今天大環境怎麼樣、全市場溫度。

```
┌─────────────────────────────────────────────────────────┐
│  台股市場總覽  2026-07-04  13:30                         │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ 景氣燈號  │ 加權指數 │ 今日漲跌 │ USD/TWD  │  美債 10Y   │
│   🟢 綠燈 │  22,450  │ +1.2%   │  31.8    │   4.35%     │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│ 三大法人今日                                              │
│   外資：+85億  投信：+12億  自營：-3億  合計：+94億       │
├─────────────────────────────────────────────────────────┤
│ 市場廣度                                                  │
│   漲家：650  跌家：280  平盤：120  漲停：23  跌停：2      │
├─────────────────────────────────────────────────────────┤
│ 市場環境判斷：多頭 ✅  建議操作強度：積極                  │
└─────────────────────────────────────────────────────────┘
```

功能細節：
- [ ] `src/dashboard/pages/market_overview.py`
- [ ] 每 30 分鐘自動更新（交易時間內）；收盤後顯示日終數據
- [ ] 三大法人近 10 日折線圖（看趨勢是持續買超還是反轉）
- [ ] 景氣燈號近 12 個月走勢（判斷現在在哪個週期）

---

#### 頁面二：個股 K 線分析

**觀察的是**：選定一支股票，看技術面是否符合買進條件。

```
輸入股票代碼：[2330]  時間區間：[6個月 ▼]  [查詢]

┌─────────────────────────────────────────────────────────┐
│  台積電 (2330)   現價：930  今日：+1.5%                  │
├─────────────────────────────────────────────────────────┤
│  [K線圖 + MA5/20/60]                                    │
│                                     ↑ MA金叉訊號         │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
├─────────────────────────────────────────────────────────┤
│  [MACD 子圖]          [RSI 子圖]        [成交量]          │
├─────────────────────────────────────────────────────────┤
│  技術面訊號                                               │
│   ✅ 站上 MA20    ✅ MACD 金叉    ✅ RSI 55（健康區間）   │
│   ✅ 放量突破（今量 = 1.8 倍均量）                        │
│   ⚠️ 布林通道上軌附近（短線稍謹慎）                       │
├─────────────────────────────────────────────────────────┤
│  籌碼面（近 10 日）                                       │
│   外資：連買 7 日 +450億   投信：連買 3 日 +28億          │
│   融資餘額：1.2%（佔流通股本，低，籌碼穩定）              │
├─────────────────────────────────────────────────────────┤
│  基本面速查                                               │
│   ROE：25%  月營收 YoY：+18%  F-score：8/9              │
│   建議進場區間：920–940   停損：860（-7%）                │
└─────────────────────────────────────────────────────────┘
```

功能細節：
- [ ] `src/dashboard/pages/stock_analysis.py`
- [ ] plotly 互動 K 線（可縮放、可 hover 看每日數據）
- [ ] 三大法人買賣超疊加在 K 線下方（綠柱 = 買、紅柱 = 賣）
- [ ] 技術訊號自動用顏色標記（✅ 符合 / ⚠️ 注意 / ❌ 不符合）
- [ ] 自動計算進場區間 + ATR 停損位

---

#### 頁面三：每週選股結果

**觀察的是**：本週系統掃完全市場後，推薦哪幾檔、為什麼、怎麼配。

```
本週選股推薦  （最後更新：2026-07-04 14:00）
市場環境：多頭 ✅   操作強度：積極

┌────┬────────┬──────┬───────────────────────┬──────┬──────┬──────┐
│排名│ 股票   │ 評分 │  推薦理由（三層摘要）  │進場價│ 停損 │配置% │
├────┼────────┼──────┼───────────────────────┼──────┼──────┼──────┤
│ 1  │2330 台積│ 87  │外資連買7日/MACD金叉/  │ 920  │ 860  │ 20%  │
│    │        │      │月營收YoY+18%           │~940  │      │      │
├────┼────────┼──────┼───────────────────────┼──────┼──────┼──────┤
│ 2  │2454 聯發│ 81  │投信+外資同買/RSI 52/  │1100  │1020  │ 15%  │
│    │        │      │F-score 8              │~1130 │      │      │
└────┴────────┴──────┴───────────────────────┴──────┴──────┴──────┘

[點擊任一列 → 跳到個股 K 線分析]

投組配置圓餅圖：
  台積電 20% ██████
  聯發科 15% █████
  ...
  現金    X% （大盤不對時自動留現金）

[下載 CSV]  [重新執行掃描]
```

功能細節：
- [ ] `src/dashboard/pages/screening_results.py`
- [ ] 可篩選（只看電子 / 只看 ROE > 20% / 只看法人買超）
- [ ] 點擊股票代碼直接跳轉到第二頁個股分析
- [ ] 投組配置圓餅圖（pyportfolioopt 結果視覺化）
- [ ] 顯示上次執行時間；按鈕手動觸發重新掃描

---

#### 啟動方式

```bash
# 安裝
uv add streamlit

# 啟動
streamlit run src/dashboard/app.py

# 瀏覽器自動開啟 http://localhost:8501
```

目錄結構新增：
```
src/
└── dashboard/
    ├── app.py                  # 主入口，定義三個頁面
    ├── pages/
    │   ├── market_overview.py  # 頁面一：市場總覽
    │   ├── stock_analysis.py   # 頁面二：個股 K 線
    │   └── screening_results.py # 頁面三：選股結果
    └── components/
        ├── kline_chart.py      # 可重用的 K 線圖元件
        └── signal_badge.py     # 技術訊號顏色標籤元件
```

- [ ] 驗收：`streamlit run src/dashboard/app.py` 能同時看到三個頁面，K 線可縮放互動，選股表可排序過濾

---

## 資料流設計

```
【第一層：總體環境】
data.gov.tw  → 景氣燈號
yfinance     → USD/TWD
FRED         → 美債 10Y
TWSE OpenAPI → 漲跌家數
        └── macro/context.py → 市場環境分類（多頭/空頭/盤整）
                └── 決定本週操作強度

【第二層：基本面篩選】
CasualMarket MCP
    └── /financial/statements → EPS, ROE, 毛利率
    └── /financial/revenue    → 月營收 YoY
    └── /financial/dividend   → 殖利率
            └── health.py (Piotroski F-score, FCF 轉換率, Altman Z)
                    └── screening/fundamental.py → 排除地雷股

【第三層：籌碼面確認】
FinMind API
    └── TaiwanStockInstitutionalInvestorsBuySell → 三大法人
    └── TaiwanStockMarginPurchaseShortSale       → 融資融券
            └── screening/chip.py → 法人買超確認

【第四層：技術面擇時】
twstock.Stock('2330')
    └── fetch_from(year, month) → data/raw/2330.parquet
            └── add_indicators(df)       ← TA-Lib
                    └── screening/technical.py → 買進訊號
                            └── ATR 停損計算  → 賣出訊號

【整合輸出】
scorer.py（四層加權評分）
    └── 每週 TOP 20 候選股
            └── pyportfolioopt → 配置比例
                    └── Telegram 推播（每週五 13:30 後）
```

---

## 台股特有注意事項

| 項目 | 說明 |
|------|------|
| 交易單位 | 1 張 = 1000 股，零股另計 |
| 手續費 | 買賣各 0.1425%（券商可能有折扣）|
| 證交稅 | 賣出 0.3%（ETF 0.1%，期貨另計）|
| 漲跌停板 | ±10%（部分商品不同）|
| 交易時間 | 09:00–13:30，週六日休市 |
| 結算 | T+2 交割 |
| TWSE rate limit | 每 5 秒最多 3 個 request |
| 上市代碼 | 4 碼數字（TWSE）；上櫃同樣 4 碼但交易所不同（TPEX）|
| 財報週期 | Q1 三月、Q2 八月、Q3 十一月、Q4/年報 隔年三月 |
| 月營收 | 每月 10 日前公布，是最即時的基本面訊號 |
| 法說會 | 通常在財報後 1–2 週，時間不固定需手動追蹤 |
| 推播通知 | LINE Notify 已於 2025 年 4 月停止服務，改用 Telegram Bot |

---

## 當前狀態與下一步行動

### 環境已就緒（2026-06-27）
所有套件已安裝完成。詳見 `pyproject.toml`。

### 待辦（Phase 1 起點）

**程式碼起點**：
```bash
mkdir -p src/data src/indicators src/strategies src/backtest src/screening src/portfolio src/macro src/sentiment src/alerts src/events src/report
mkdir -p data/raw data/processed data/chip data/macro data/universe
touch src/__init__.py src/data/__init__.py
```
然後從 `src/data/fetcher.py` 開始，先讓 twstock 能抓 2330 的歷史 K 線。
