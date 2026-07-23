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
- 趨勢（必要）：站上 20MA 且 20MA > 60MA；MACD 零軸以上或金叉剛形成
- 動能（至少一）：RSI 40–70；KD 金叉且 K < 80
- 量能（必要）：突破時成交量 > 5 日均量 1.5 倍
- K 線型態加分（選配）：晨星、錘子線、吞噬（TA-Lib）

**賣出**（觸發任一）：
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

**目標**：能穩定拿到資料、歷史資料落地本機、批次掃描不打爆外部 API。抓取一律經中台（`data_service/`），`src/` 不直打外部來源。

#### 1a. 中台快取持久化（SQLite，設計定稿 2026-07-23）

現況記憶體 TTL cache 重啟即空。升級為**兩層**：記憶體管秒級即時（五檔/分時/即時指數/分鐘 K，**不落地**——即時資料落地只是存垃圾），SQLite 管歷史（日/週/月 K 線——指標/評分/回測讀最兇的資料）。

- [ ] `data_service/store.py`：SQLite 讀寫層。檔案放 `data/cache.db`（WAL mode、gitignored），schema：

  ```sql
  CREATE TABLE candles (
    ticker     TEXT NOT NULL,   -- yfinance 代碼，如 '2330.TW'
    interval   TEXT NOT NULL,   -- '1d' / '1wk' / '1mo'（分鐘線不落地）
    ts         TEXT NOT NULL,   -- 交易日 'YYYY-MM-DD'
    open  REAL NOT NULL, high REAL NOT NULL,
    low   REAL NOT NULL, close REAL NOT NULL,
    volume INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,   -- 寫入時間（UTC ISO）
    PRIMARY KEY (ticker, interval, ts)
  ) WITHOUT ROWID;
  ```

- [ ] `sources/stock.py` K 線函式改三步查找：記憶體 TTL 60s（不變）→ SQLite 查已存區間 → 只跟 yfinance 要缺口（從庫內最後 5 根**重疊**抓起）→ upsert 回存 → 回傳
  - 重疊 5 根是**除權息偵測**：庫內 close 與新抓 close 相對差 >0.1% → 還原價已平移，該股整段重抓覆寫（台股 7–9 月除權息旺季，這不是邊角案例）
  - 當日 K 棒盤中會變：upsert 同鍵覆寫，收盤後自然定型
  - HTTP contract 零改變：回傳 JSON 形狀與改動前逐欄位一致
- [ ] `data/` 加進 `.gitignore`（快取是可再生的衍生資料）
- [ ] 驗收：重啟服務後同一支 K 線 API 第二次請求只向 yfinance 要尾巴（日誌可見）；改動前後回傳 JSON diff 為空；`git status` 看不到 `data/`

#### 1b. 其餘資料管線

- [ ] `src/data/universe.py`：股票清單（上市 + 上櫃），從 twstock codes 產生（本地查表，不經中台）；驗收：`python -m src.data.universe` 印出上市/上櫃檔數
- [ ] ~~`src/data/fetcher.py`、`src/data/store.py`（Parquet）~~ 已由中台取代（抓取唯一入口是 `data_service/`）；Parquet 降級為未來「回測批次匯出」的可選格式，需要時再加
- [ ] `src/data/fundamental.py`：CasualMarket MCP 拉財務資料（併入 Phase 4 一起做）

**限制**：twstock 對 TWSE 每 5 秒最多 3 request，批次下載要 sleep；FinMind 免費 600 req/hr。

### Phase 2 — 技術指標模組（第四層）

- [ ] `src/indicators/trend.py`（SMA/EMA/MACD）、`momentum.py`（RSI/KD/Williams %R）、`volatility.py`（ATR/布林）、`volume.py`(OBV/量比)、`pattern.py`（TA-Lib 61 型態）
- [ ] 統一介面 `add_indicators(df) -> df`
- [ ] 驗收：notebook 畫出含 MACD、RSI、布林的完整圖

### Phase 3 — 策略回測（驗證第四層）

- [ ] `src/strategies/base.py`：繼承 backtesting.py `Strategy`，加台股邏輯（整張 1000 股、漲跌停）
- [ ] 三個策略：`ma_cross.py`、`rsi_reversal.py`（+ATR 停損）、`macd_trend.py`（+量能過濾）
- [ ] `src/backtest/`：runner（`commission=0.001425`）、optimizer（grid search，小心 overfitting）、metrics（年化/Sharpe/最大回撤/勝率/盈虧比）
- [ ] 驗收：2330 跑 2020–2025 回測，輸出交易紀錄與績效摘要
- **回測必含交易成本**：手續費買賣各 0.1425%、賣出證交稅 0.3%（ETF 0.1%）

### Phase 4 — 基本面整合（第二層）

- [ ] CasualMarket：`/financial/statements`（EPS/ROE/毛利率）、`/revenue`（月營收 YoY）、`/dividend`（殖利率）
- [ ] `src/indicators/health.py`：Piotroski F-score、FCF 轉換率、Altman Z-score（自建，無現成台股套件）
- [ ] `src/screening/fundamental.py`：硬性門檻篩選
- [ ] 驗收：能從全市場篩出基本面合格的候選清單

### Phase 5 — 籌碼面與總體環境（第一、三層）

- [ ] `src/data/chip.py`：FinMind `TaiwanStockInstitutionalInvestorsBuySell`、`TaiwanStockMarginPurchaseShortSale`
- [ ] `src/data/macro.py`：景氣燈號（data.gov.tw #6099）、USD/TWD（yfinance）、美債 10Y（FRED `DGS10`）、漲跌家數（TWSE OpenAPI）
- [ ] `src/macro/context.py`：總體指標 → 多頭/空頭/盤整分類
- [ ] `src/screening/chip.py` + `src/screening/scorer.py`：四維度加權評分
- [ ] 驗收：同一支股票在不同總體環境下排名不同

### Phase 6 — 選股系統、投組優化與排程

- [ ] `src/screening/technical.py`：技術面條件集合
- [ ] 批次掃描：每週輸出 TOP 20 候選股 CSV + 摘要
- [ ] `src/portfolio/optimizer.py`：pyportfolioopt 均值-方差 / 風險平價，單股上限 20%
- [ ] `src/alerts/`：feedparser 監控 TWSE 重大訊息、APScheduler（本機測試）、Telegram 推播
- [ ] GitHub Actions 正式排程（workflow 骨架見 todo.md）
- [ ] 驗收：一行指令輸出本週推薦清單＋配置比例，並推播 Telegram

### Phase 7 — 因子分析與事件研究

- [ ] alphalens-reloaded 分析因子 IC/IR、最佳持有週期
- [ ] `src/events/study.py`：自建事件研究（市場模型 OLS 估 alpha/beta → AR → CAR → t 檢定）
- [ ] 驗收：能輸出「外資連買 5 日後，10 日平均 CAR = X%（p < 0.05）」這類結論

### Phase 8 — 情緒面整合（選配）

- [ ] `src/sentiment/trends.py`：pytrends 搜尋熱度
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
CasualMarket MCP（statements / revenue / dividend）
        └── health.py（F-score, FCF, Altman Z）
                └── screening/fundamental.py → 排除地雷股

【第三層：籌碼面確認】
FinMind（法人買賣超 / 融資券）
        └── screening/chip.py → 法人買超確認

【第四層：技術面擇時】
中台 raw candles → add_indicators()（TA-Lib）
        └── screening/technical.py → 買進訊號 → ATR 停損 → 賣出訊號

【整合輸出】
scorer.py（四層加權評分）
    └── 每週 TOP 20 候選股
            └── pyportfolioopt → 配置比例
                    └── Telegram 推播（每週五收盤後）
```

## 目錄結構（`src/` 藍圖，Phase 1–8 逐步建立）

`frontend/`（前端）與 `data_service/`（中台）已存在；以下是還沒建的計算層：

```
src/
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
