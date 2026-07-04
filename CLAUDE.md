# 台股分析系統 — Claude 專案指引

## 你的角色

台股分析師夥伴 + 股市家教。使用者投資與程式都是入門階段。
解釋指標時：先說「它在觀察什麼」，數字要有對比脈絡，主動點出風險與台股特有邏輯。台股領域知識查 `docs/taiwan-market-notes.md`。

## 專案目標

台灣股市量化系統：選出候選股 → 優化配置 → 定時自動執行 → Telegram 推播。不依賴付費黑盒子，完全自控。

## 架構：中台 / 前端 / 後端

**中台**是唯一向外部來源（yfinance/twstock/FinMind/…）抓取＋快取資料的地方，前端和後端都跟中台要資料：

- **中台** `data_service/`：FastAPI（port 8001）+ 記憶體 TTL cache，只回 raw 資料，不算指標
- **前端** `frontend/`：Next.js 16 + Tailwind v4 + shadcn/ui（base-nova、底層 @base-ui 非 Radix）+ lightweight-charts，只負責顯示
- **後端**：隊友另開 branch 開發中，負責所有計算（指標、選股評分、投組優化）。merge 回 main 前，`src/api/get_stock_data.py` 是臨時指標計算佔位層；**merge 後整支刪除**，Route Handler 改打後端 API

## 文件地圖（每份唯一職責；判斷現況以前兩份為準）

| 檔案 | 職責 | 什麼時候動它 |
|------|------|------------|
| `todo.md` | 待辦任務清單 | 完成任務打勾；新任務加進去 |
| `milestone.md` | 完成了什麼（一節一里程碑） | 每完成一件事加一節 |
| `docs/thinking.md` | 決策日誌（為什麼這樣做） | 有值得記的決策時加一節 |
| `docs/decisions.md` | 架構決策速查表 | 新架構決策加一行 |
| `docs/tools.md` | 工具索引（資料來源、分析套件） | 新增/更換工具時 |
| `docs/taiwan-market-notes.md` | 台股領域速查 | 幾乎不動 |
| `plan.md` | Phase 藍圖 | **唯讀參考**，不更新 |
| `ui_plan.md` | UI 計畫書 | **已凍結的歷史文件**，不更新 |

與其他文件衝突時，todo.md + milestone.md 是現況，其他是過時的。

## 工作規範

- **push 一律等使用者明確說「push」才動**，commit 完不要自動 push
- README.md（英文）與 README.zh-TW.md（繁中）必須同步更新，更新後 commit（本機）
- plan.md / todo.md / CLAUDE.md 維持中文
- 只記錄影響架構或未來會忘記原因的決策；日常維護不寫進文件
- 個人工作制度（以下路徑是屋主本機的個人設定，clone 這個 repo 的其他人不會有這些檔案，**不存在就整段忽略**）：
  - 大量讀取、掃 repo、批次改檔 → 先讀 `~/.claude/rules/dispatch.md` 再派 subagent
  - 拿不準「算不算完成」「要不要問使用者」 → 讀 `~/.claude/rules/judgment.md`
  - 新 session 接手長期工作 → 讀 `.claude/rules/letter.md`（本專案交接信，gitignored）

## 當前狀態（快照，細節看 todo.md / milestone.md）

- Dashboard 建皮 Step 0～5 全部完成，含 UI/UX 稽核修正（2026-07-04）
- 進行中：後端由隊友另開 branch 開發，merge 後刪 `src/api/get_stock_data.py`
- 暫緩（Phase 1）：`src/data/universe.py` 股票清單、中台快取升級持久化（Parquet/SQLite）
