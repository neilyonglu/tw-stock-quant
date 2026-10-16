# 未來 Phase 藍圖

> 本檔只放**還沒做**的規劃。現況與已完成見 `PROJECT.md`，待辦見 `todo.md`。
> 工具選型見 PROJECT.md 工具索引；台股費率/慣例見 `docs/taiwan-market-notes.md`。

**最終目標**：系統定期掃全市場，輸出「可以買哪檔股票、在什麼時機買賣」的可操作建議。

---

## 投資決策框架（系統大腦）

每一個 Phase 都在為這個框架的某一層提供材料。

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

### 第一層：總體環境 — 現在適合操作嗎？

| 指標 | 觀察什麼 | 影響 |
|------|----------|------|
| 景氣燈號（國發會） | 紅燈=過熱、藍燈=衰退、綠燈=正常 | 藍燈區間降低持股比例 |
| 美債 10Y 殖利率 | 快速走升代表資金成本增加 | 成長股估值承壓，減少高本益比標的 |
| USD/TWD 匯率 | 外資匯率收益影響進出意願 | 台幣大幅貶值時，外資容易撤出 |
| 市場廣度（漲跌家數） | 多數股票在漲 vs 只有少數在漲 | 廣度萎縮是行情末段警訊 |

> USD/TWD 特別重要：台積電、聯發科收入以美元計價，USD/TWD 每動 1 元，台積電季 EPS 差約 0.3–0.5 元；USD 走強時外資傾向撤出新興市場。

**判斷結果**：多頭（景氣綠燈以上、美債穩定）→ 滿倉積極；盤整（訊號混雜）→ 半倉只選最強；空頭（藍燈、外資大賣）→ 縮手持現金。

### 第二層：基本面初篩 — 這家公司值得研究嗎？

**硬性門檻（不符合就排除）**：
- ROE > 12%；近 4 季 EPS 均為正；月營收近 3 個月 YoY > 0%；Piotroski F-score ≥ 6

**加分項（提高排名）**：
- 月營收 YoY > 10%；FCF 轉換率 > 80%；殖利率 > 4%；Altman Z-score > 2.99

### 第三層：籌碼面確認 — 有大戶在買嗎？

| 籌碼訊號 | 意義 | 操作含義 |
|----------|------|----------|
| 外資連續買超 5 日以上 | 外資認同 | 加分 |
| 投信連續買超（月底前） | 基金建倉 | 加分，特別是季報前 |
| 外資 + 投信同步買 | 法人齊買 | 強力加分 |
| 融資餘額大幅攀升 | 散戶借錢追高 | 減分，小心反轉 |
| 融券大增 | 有人放空 | 注意，但回補也會拉升 |

**排除條件**：融資餘額佔流通股本 > 5%（過度散戶化，籌碼不穩定）

### 第四層：技術面擇時 — 什麼時候進？什麼時候出？

**買進**（需同時符合）：

單股 technical-v1 已實作下列技術門檻，僅代表技術篩選通過；分數權重、交叉定義、排除當日 K 的限制見 [技術篩選規格](docs/technical-screening.md)。尚未合併前三層資料，也未驗證為可獲利策略。
- 趨勢（必要）：站上 20MA 且 20MA > 60MA；MACD 零軸以上或金叉剛形成
- 動能（至少一）：RSI 40–70；KD 金叉且 K < 80
- 量能（必要）：本根成交量 > 前 5 根日 K 均量 1.5 倍（不含本根）；v1 不另宣稱突破事件
- K 線型態加分（選配）：晨星、錘子線、吞噬（TA-Lib）

**賣出**（後續持倉／回測模組，尚未實作；觸發任一）：
- 止損（優先）：跌破進場價 7%；跌破 20MA 且放量；ATR 停損（進場價 − 2×ATR）
- 獲利出場：RSI > 75 且回頭；MACD 死叉且放量；月營收連 3 個月 YoY 轉負

### 輸出格式

每週五收盤後產出：

```
== 本週選股推薦（YYYY-MM-DD） ==
總體環境：多頭 ✅　推薦操作強度：積極

| 排名 | 股票 | 買進理由（三層）| 建議進場區間 | 停損 | 配置比例 |
| 1 | 2330 台積電 | 法人連買 7 日 / RSI 52 / MACD 金叉 | 900–920 | 860 | 20% |
...
風險提示：本清單僅為參考，不構成投資建議。
```

---

## 開發計畫（Phase 對應四層框架）

### Phase 1 — 資料管線（第一優先）

**目標**：能穩定拿到資料、歷史資料落地本機、批次掃描不打爆外部 API。抓取一律經中台（`backend/data_service/`），`backend/` 不直打外部來源。

#### 1a. 中台快取持久化 — ✅ 完成（2026-07-23）

SQLite 兩層快取上線。最終狀態、schema 與踩坑（yfinance 還原價抖動、period 左緣語意）見 PROJECT.md 架構段與「資料層」踩坑。

#### 1b. 其餘資料管線

- [x] `backend/data/universe.py`：一般股票清單（上市＋上櫃），從 twstock codes 本地快照產生；`uv run python -m backend.data.universe` 印出兩市場檔數。
- [x] 共用 `yahoo_symbol()`，K 線／分時／基本面／前收盤及 SQLite 鍵依市場選 `.TW`／`.TWO`；兩市場測試與實際 Docker 驗收通過。
- [ ] 用股票清單建立批次掃描與頻率控制，保留來源缺值／失敗狀態，批次套用單股技術篩選。
- [ ] ~~`backend/data/fetcher.py`、`backend/data/store.py`（Parquet）~~ 已由中台取代（抓取唯一入口是 `backend/data_service/`）；Parquet 降級為未來「回測批次匯出」的可選格式，需要時再加
- [x] `backend/data_service/sources/fundamental.py`：FinMind 五類原始財務資料（Phase 4 資料入口），不另建計算層 fetcher

**限制**：twstock 對 TWSE 每 5 秒最多 3 request，批次下載要 sleep；FinMind 免費 600 req/hr。

### Phase 2 — 技術指標模組（第四層）— 已由 PR #7 合併

共用入口為 `backend.indicators.add_indicators`，個股 API 以 `backend.api.get_stock_data` 模組組裝 JSON。[PR #7](https://github.com/neilyonglu/tw-stock-quant/pull/7) 已合併；部署結果仍依 main Actions 實際結果驗收。

- [x] SMA/EMA/MACD、RSI/KD、ATR、均量／量比、TA-Lib 型態辨識；Williams %R／布林／OBV 等尚未使用的指標留待實際規則需要再加。
- [x] 統一介面 `add_indicators(df) -> df`，個股 wrapper 保留既有欄位並新增 `kd`、`atr14`、`stale_adjust` 合約。
- [x] KD／ATR 接入圖表與速查，補齊定義、週期、缺值與算法差異說明；控制欄保留捲動但不顯示捲軸。
- [x] 價格還原失敗在計算前阻擋，API 回 503，前端隱藏舊資料並自動恢復。
- [x] 23 個 Python 測試、Node 檢查、正式／Docker 建置及手機／桌面流程；公開公式與參考數值結果見 [指標驗證](docs/indicator-review.md)。
- [ ] 抽樣 2330 與指定券商介面逐筆比對：需要同批 OHLCV、還原、起始時間及參數；不可將公式核對或 TA-Lib 測試當成已對齊實際券商畫面。

### Phase 3 — 策略回測（驗證第四層）

- [ ] `backend/strategies/base.py`：繼承 backtesting.py `Strategy`，加台股邏輯（整張 1000 股、漲跌停）
- [ ] 三個策略：`ma_cross.py`、`rsi_reversal.py`（+ATR 停損）、`macd_trend.py`（+量能過濾）
- [ ] `backend/backtest/`：runner（`commission=0.001425`）、optimizer（grid search，小心 overfitting）、metrics（年化/Sharpe/最大回撤/勝率/盈虧比）
- [ ] 驗收：2330 跑 2020–2025 回測，輸出交易紀錄與績效摘要
- **回測必含交易成本**：手續費買賣各 0.1425%、賣出證交稅 0.3%（ETF 0.1%）

### Phase 4 — 基本面整合（第二層）

- [x] FinMind：損益表／資產負債表／現金流量表／月營收／股利，經中台 `/stocks/{ticker}/fundamentals` 分類取原始資料。CasualMarket 提供 MCP 工具，原先列的 REST 路徑未經確認，不作為介面。
- [ ] 核對科目、單季／累計與單位，明訂 ROE 期間、FCF 轉換率及 F-score／Altman 適用範圍；缺值與公告日期不得猜測
- [x] `backend/indicators/fundamental.py`：TTM ROE、營收 YoY、F-score 九項研究計算；缺訊號不湊分，兩檔指定年度以官方財報人工核對補足長債與普通股發行，其他股票／年度仍待補
- [x] 個股基本面前端呈現研究指標／訊號、期間與品質、人工來源註記，月營收換真；未將每週選股多因子示範合約冒充真實篩選
- [ ] FCF 轉換率、Altman Z-score 加分項及資料口徑
- [x] `backend/screening/fundamental.py` + `backend.api.screen_fundamental`：四項研究門檻、連續期間、缺值及品質限制；尚非完整已驗證篩選，passed=null，見 docs/fundamental-screening.md
- [ ] 驗收：能從全市場篩出基本面合格的候選清單

### Phase 5 — 籌碼面與總體環境（第一、三層）

- [ ] `backend/data/chip.py`：FinMind `TaiwanStockInstitutionalInvestorsBuySell`、`TaiwanStockMarginPurchaseShortSale`
- [ ] `backend/data/macro.py`：景氣燈號（data.gov.tw #6099）、USD/TWD（yfinance）、美債 10Y（FRED `DGS10`）、漲跌家數（TWSE OpenAPI）
- [ ] `backend/macro/context.py`：總體指標 → 多頭/空頭/盤整分類
- [ ] `backend/screening/chip.py` + `backend/screening/scorer.py`：四維度加權評分
- [ ] 驗收：同一支股票在不同總體環境下排名不同

### Phase 6 — 選股系統、投組優化與排程

- [x] `backend/screening/technical.py`：單股技術條件、0–100 符合度、各項理由及無法評分狀態；`backend.api.screen_stock` 經中台取日 K，55 項測試及兩市場實際 Docker 驗收通過
- [ ] 技術面規則回測／權重校準、持倉與賣出規則，以及總體／基本面／籌碼綜合評分
- [ ] 批次掃描：每週輸出 TOP 20 候選股 CSV + 摘要
- [ ] `backend/portfolio/optimizer.py`：pyportfolioopt 均值-方差 / 風險平價，單股上限 20%
- [ ] `backend/alerts/`：feedparser 監控 TWSE 重大訊息、APScheduler（本機測試）、Telegram 推播
- [ ] GitHub Actions 正式排程（workflow 骨架見 todo.md）
- [ ] 驗收：一行指令輸出本週推薦清單＋配置比例，並推播 Telegram

### Phase 7 — 因子分析與事件研究

- [ ] alphalens-reloaded 分析因子 IC/IR、最佳持有週期
- [ ] `backend/events/study.py`：自建事件研究（市場模型 OLS 估 alpha/beta → AR → CAR → t 檢定）
- [ ] 驗收：能輸出「外資連買 5 日後，10 日平均 CAR = X%（p < 0.05）」這類結論

### Phase 8 — 情緒面整合（選配）

- [ ] `backend/sentiment/trends.py`：pytrends 搜尋熱度
- [ ] PTT 情緒：爬蟲 + Claude API 判斷正負（不用本地 NLP）
- [ ] 併入 scorer.py 低權重輔助因子

### Phase 9 — Dashboard 接真資料與部署

建皮（介面框架）已完成，見 PROJECT.md。剩餘：

- [ ] 前端 mock 欄位換真資料（大部分待後端 merge 與 Phase 1/4/5，見 todo.md）
- [ ] 部署：前端 Vercel、中台＋後端 Railway 或 Render（免費 tier）

---

## 資料流設計

```
【第一層：總體環境】
data.gov.tw / yfinance / FRED / TWSE OpenAPI
        └── macro/context.py → 市場環境分類 → 決定本週操作強度

【第二層：基本面篩選】
FinMind → 中台 /stocks/{ticker}/fundamentals（五類 raw；已接入）
                └── indicators/fundamental.py（ROE／YoY／F-score；FCF、Altman 尚未做）
                └── screening/fundamental.py → 單股研究條件，品質與缺項仍限制判定

【第三層：籌碼面確認】
FinMind（法人買賣超 / 融資券）
        └── screening/chip.py → 法人買超確認

【第四層：技術面擇時】
中台 raw candles → add_indicators()（TA-Lib）
        └── screening/technical.py → 單股規則／分數／理由（已實作）
                └── ATR 停損／持倉／賣出訊號（待實作）

【整合輸出】
scorer.py（四層加權評分）
    └── 每週 TOP 20 候選股
            └── pyportfolioopt → 配置比例
                    └── Telegram 推播（每週五收盤後）
```

## 目錄結構（`backend/` 藍圖，Phase 1–8 逐步建立）

`frontend/`（前端）與 `backend/data_service/`（中台）已存在；以下是還沒建的計算層：

```
backend/
├── api/         # 已存在：個股計算入口 get_stock_data.py
├── data_service/ # 已存在：資料抓取、TTL、SQLite，中台唯一入口
├── data/        # fetcher, store(Parquet), fundamental, chip, macro, universe
├── indicators/  # trend, momentum, volatility, volume, pattern, health
├── strategies/  # base(台股邏輯), ma_cross, rsi_reversal, macd_trend, fundamental_mom
├── backtest/    # runner, optimizer, metrics
├── screening/   # technical, fundamental, chip, scorer
├── portfolio/   # optimizer（pyportfolioopt）
├── macro/       # context（第一層判斷）
├── sentiment/   # trends, nlp（Phase 8）
├── events/      # study（Phase 7）
├── alerts/      # scheduler, notify
└── report/      # chart, summary

data/            # raw / processed / chip / macro / universe（Parquet）
```
