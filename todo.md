# 待辦

> Dashboard 建皮（Step 0–5）已全部完成，成果見 `PROJECT.md`。Phase 1–8 細節見 `plan.md`。

## 現在就可以做（不依賴後端）

- [ ] 中台快取升級持久化（Parquet/SQLite），取代記憶體 TTL cache——這是 `data_service/` 自己的範圍，跟後端隊友的 branch 無關，不要誤判成要等
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

## 待後端 merge（隊友 branch 合回 main 時逐項核對）

- [ ] 刪除 `src/api/get_stock_data.py`（臨時指標計算佔位層）
- [ ] `app/api/stock/[ticker]/route.ts` 改打後端 API（JSON 形狀不變，前端元件零改動）
- [ ] `frontend/src/lib/types.ts` 的 mock 合約與真後端回傳對齊
- [ ] 前端剩餘 mock 欄位換真實 API：選股結果頁、三大法人、市場廣度、排行榜、籌碼 Tab、月營收、K 線型態等（完整清單見 PROJECT.md 真實 vs mock 對照表）
- [ ] `main.py` 能單獨跑完整選股流程並推播 Telegram
- [ ] GitHub Actions 手動觸發驗收（依賴上一項）

## 刻意不做（避免範圍無限擴大）

看盤平台常見但暫不跟進：同類股/概念股比較、注意股/處置股清單、社群討論/多空投票、警示燈號標記。
