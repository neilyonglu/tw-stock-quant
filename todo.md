# 待辦

> Dashboard 建皮（Step 0–5）已全部完成，成果見 `PROJECT.md`。Phase 1–8 細節見 `plan.md`。
> 分工（2026-07-23 與隊友確認）：隊友 branch 只做**回測系統**；技術指標、選股評分、投組優化歸本專案。

## 現在就可以做（不依賴隊友）

- [x] 中台快取持久化（SQLite）——2026-07-23 完成，最終狀態見 PROJECT.md 架構段
- [x] 自選股清單＋市場/個股頁面定期自動刷新——2026-07-29 完成（branch `feature/watchlist-live-refresh`），最終狀態見 PROJECT.md
- [x] 自選股頁改 App 風格（sparkline）＋個股首頁排行榜（示範資料）＋K 線今日按鈕——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 查無股票代碼錯誤畫面＋股票關鍵字搜尋＋修切換代碼殘留舊資料 bug——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 全 repo 稽核＋修掉三條「假資料看起來像真的」——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [ ] **👉 下一個：指標計算層扶正**——`src/api/get_stock_data.py` 從臨時佔位改為正式模組。步驟：
  1. 規劃位置與呼叫方式（`src/indicators/` 模組化 vs 隨 Route Handler 續用 execFile，先出方案再動手）
  2. SMA/EMA/RSI/MACD 等既有指標搬家＋補驗證（抽樣手算對照，見 judgment 品質底線）
  3. K 線型態辨識一併解決 TA-Lib 環境問題（見 PROJECT.md「兩個 Python 環境」），mock 換真
  4. Route Handler 的 JSON 形狀不變，前端元件零改動（合約見 `frontend/src/lib/types.ts`）
- [ ] 中台支援上櫃股：ticker 目前寫死 `.TW`（`data_service/sources/stock.py`），上櫃股（`.TWO`）抓不到 K 線——全市場掃描前必須修（twstock codes 可查上市/上櫃別，據此選後綴）
- [ ] 選股評分與投組優化（Phase 藍圖見 plan.md）；完成後 `/api/screening` mock 換真、`frontend/src/lib/types.ts` 合約對齊
- [ ] 前端剩餘 mock 欄位換真實 API：三大法人、市場廣度、排行榜、籌碼 Tab、月營收等（完整清單見 PROJECT.md 真實 vs mock 對照表；依賴各 Phase 資料源接入）
- [ ] `main.py` 能單獨跑完整選股流程並推播 Telegram（依賴指標＋評分完成）
- [ ] GitHub Actions workflow 骨架：建 `.github/workflows/weekly_scan.yml`

  ```yaml
  name: 每週選股掃描
  on:
    schedule:
      - cron: '0 6 * * 5'   # UTC 06:00 = 台灣時間週五 14:00（收盤後）
    workflow_dispatch:        # 也可手動觸發
  jobs:
    scan:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v3
        - run: uv sync
        - run: uv run python main.py
          env:
            FINMIND_TOKEN: ${{ secrets.FINMIND_TOKEN }}
            TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
            TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  ```

- [ ] GitHub repo Settings → Secrets → Actions 新增：`FINMIND_TOKEN`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`
- [ ] `src/alerts/scheduler.py`（Phase 6 建立時）定位為本機測試用，正式排程走 GitHub Actions
- [ ] GitHub Actions 手動觸發驗收（依賴 `main.py` 完整流程）

## 稽核發現、還沒修的（2026-07-29 全 repo 稽核，依嚴重度排序）

當次只修了「假資料看起來像真的」三條（見上方已完成項），以下是同一次稽核記錄下來、還沒處理的：

- [ ] **API 失敗會白屏**：`market-overview-view.tsx` 與 `stock/profile-tab.tsx` 沒檢查 `res.ok` 就把回應塞進 state，中台掛掉時 render 存取 undefined 會整頁崩潰。`stock-analysis-view.tsx` 已有正確寫法可照抄
- [ ] **漲跌停價短區間會靜默算錯**：`data_service/sources/stock.py` 的 `_render()` 拿「過濾後清單的前一筆」當前收盤價，短區間（如 `period=1d`）過濾後只剩 1 根時會拿今天自己的收盤價當基準，算出錯的漲跌停但不報錯。應改用真正的前一交易日收盤
- [ ] **只有 1 根 K 棒會 IndexError**：`src/api/get_stock_data.py` 的 `prev_price = close.iloc[-2]`（新股上市首日會踩到），跟已修好的 RSI 是同一類邊界問題
- [ ] **除權息重抓失敗只寫 log**：`data_service/sources/stock.py` 重抓失敗時 API 回應沒有任何欄位標示「這批是平移前的舊還原價」，呼叫方（含隊友的回測）無從得知。建議回應加一個標記欄位
- [ ] **缺值語意不一致**：`fetch_profile()` 的 `market_cap`/`shares_outstanding` 缺值回 `0`，同函式其他欄位缺值都回 `None`。`0` 可能被誤讀成真實市值，應統一回 `None`
- [ ] **切換股票有 race condition**：6 個依 ticker 抓資料的元件（order-book、chip-tab、profile-tab、news-tab、intraday-tab、watchlist-view）沒有 AbortController，快速切換代碼時舊請求可能後到覆蓋新資料
- [ ] **色票 token 沒人用**：`globals.css` 定義了 `--stock-up`/`--stock-down` 語意色票，但 24 處各自硬寫 `text-red-400`/`text-emerald-400`；`kline-chart.tsx` 與 `intraday-chart.tsx` 還各自重複定義相同 hex 常數
- [ ] **RSI 演算法與市面平台不一致**：用簡單 rolling mean，市面（TradingView 等）用 Wilder's smoothing，數值對不上會讓人困惑。指標層扶正時一併處理
- [ ] **中台快取無鎖**：`data_service/cache.py` 的 `ttl_cache` 在並發打同一個未快取 key 時會重複打外部 API（cache stampede），目前單人使用不影響
- [ ] 清掉沒用到的程式碼：`main.py` 仍是 `Hello from stock-analysis!` 骨架；`frontend/src/lib/watchlist.ts` 有 3 個 export 沒人呼叫
- [ ] 找櫃買指數的替代資料源（TPEx OpenAPI）——yfinance `^TWOII` 已失效，目前 UI 顯示「—」

## 待隊友回測 branch merge（合回 main 時逐項核對）

- [ ] 核對她的 branch 與 `src/` 的指標/評分/優化模組**沒有重複實作**——有重疊先商量再 merge，不要兩份並存
- [ ] 回測模組接入選股流程（輸入輸出合約對齊；回測結果必含交易成本，費率見 docs/taiwan-market-notes.md）

## 刻意不做（避免範圍無限擴大）

看盤平台常見但暫不跟進：同類股/概念股比較、注意股/處置股清單、社群討論/多空投票、警示燈號標記。
