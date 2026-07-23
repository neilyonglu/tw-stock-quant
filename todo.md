# 待辦

> Dashboard 建皮（Step 0–5）已全部完成，成果見 `PROJECT.md`。Phase 1–8 細節見 `plan.md`。
> 分工（2026-07-23 與隊友確認）：隊友 branch 只做**回測系統**；技術指標、選股評分、投組優化歸本專案。

## 現在就可以做（不依賴隊友）

- [ ] 中台快取升級持久化（Parquet/SQLite），取代記憶體 TTL cache——這是 `data_service/` 自己的範圍，跟隊友的 branch 無關，不要誤判成要等
- [ ] 指標計算層扶正：`src/api/get_stock_data.py` 從臨時佔位改為正式模組（位置與呼叫方式先規劃再動手）；K 線型態辨識一併解決 TA-Lib 環境問題（見 PROJECT.md「兩個 Python 環境」）。Route Handler 的 JSON 形狀不變，前端元件零改動
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

## 待隊友回測 branch merge（合回 main 時逐項核對）

- [ ] 核對她的 branch 與 `src/` 的指標/評分/優化模組**沒有重複實作**——有重疊先商量再 merge，不要兩份並存
- [ ] 回測模組接入選股流程（輸入輸出合約對齊；回測結果必含交易成本，費率見 docs/taiwan-market-notes.md）

## 刻意不做（避免範圍無限擴大）

看盤平台常見但暫不跟進：同類股/概念股比較、注意股/處置股清單、社群討論/多空投票、警示燈號標記。
