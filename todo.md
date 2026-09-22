# 待辦

> Dashboard 建皮（Step 0–5）已全部完成，成果見 `PROJECT.md`。Phase 1–8 細節見 `plan.md`。
> 分工（2026-07-23 與隊友確認）：隊友 branch 只做**回測系統**；技術指標、選股評分、投組優化歸本專案。

## 現在就可以做（不依賴隊友）

- [x] 中台快取持久化（SQLite）——2026-07-23 完成，最終狀態見 PROJECT.md 架構段
- [x] 自選股清單＋市場/個股頁面定期自動刷新——2026-07-29 完成（branch `feature/watchlist-live-refresh`），最終狀態見 PROJECT.md
- [x] 自選股頁改 App 風格（sparkline）＋個股首頁排行榜（示範資料）＋K 線今日按鈕——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 查無股票代碼錯誤畫面＋股票關鍵字搜尋＋修切換代碼殘留舊資料 bug——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 全 repo 稽核＋修掉三條「假資料看起來像真的」——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 稽核其餘 11 項全部修完（白屏防護、漲跌停算錯、RSI 演算法、缺值語意、快取加鎖等）——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] Route Handler 改 `uv run` 執行 Python（Windows PATH 踩坑）——2026-09-20 完成，同上 branch；副作用：TA-Lib 環境障礙消失，見 PROJECT.md「Python 環境」
- [x] `feature/watchlist-live-refresh` 併回 main——2026-09-22 PR #3
- [x] 指標計算層扶正（＝Phase 2）——2026-09-22 完成，`src/indicators/` + 17 個測試，最終狀態見 PROJECT.md 架構段
- [ ] 決定 `.agents/`（archify skill 本體）與 `skills-lock.json` 要進版控還是 `.gitignore`——目前是 untracked；隊友要共用同一份 skill 就 commit，否則 ignore 各自 `npx skills add`
- [ ] 抽 2330 日線的 RSI / MACD / KD 跟你手上的券商 App 對照一次（我只對照過 TA-Lib，KD 是台股算法沒有程式對照組，要人眼確認）
- [ ] **👉 下一個：Phase 1b 收尾**——(1) 中台支援上櫃股：ticker 目前寫死 `.TW`（`data_service/sources/stock.py`），上櫃股（`.TWO`）抓不到 K 線，twstock codes 可查上市/上櫃別據此選後綴；(2) `src/data/universe.py` 股票清單（上市＋上櫃）。兩個都是全市場掃描的前提
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

## 稽核發現（2026-07-29 全 repo 稽核）

三條「假資料看起來像真的」與其餘 11 項全部處理完畢，最終狀態見 PROJECT.md。
唯一保留為待辦的是需要新資料源的那條：

- [ ] 找櫃買指數的替代資料源（TPEx OpenAPI）——yfinance `^TWOII` 已失效（實測 `^TWOII`/`^TWO`/`^TPEX` 全回 0 筆），目前中台回 `null`、UI 誠實顯示「—」

## 待隊友回測 branch merge（合回 main 時逐項核對）

> 2026-09-22 盤點：remote 上沒有隊友的 branch（只有 `dashboard-ui`、`cache-persistence`、`watchlist-live-refresh` 三條都是自己的），回測進度不明——先問一下她推到哪裡了。

- [ ] 核對她的 branch 與 `src/` 的指標/評分/優化模組**沒有重複實作**——有重疊先商量再 merge，不要兩份並存
- [ ] 回測模組接入選股流程（輸入輸出合約對齊；回測結果必含交易成本，費率見 docs/taiwan-market-notes.md）

## 刻意不做（避免範圍無限擴大）

看盤平台常見但暫不跟進：同類股/概念股比較、注意股/處置股清單、社群討論/多空投票、警示燈號標記。
