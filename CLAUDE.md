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
- **後端**（計算層）：技術指標、選股評分、投組優化由**本專案自行開發**；隊友另開 branch 只負責**回測系統**（2026-07-23 確認分工）。`src/api/get_stock_data.py` 是指標計算的起點，待扶正為正式模組（見 todo.md）

## 文件地圖（每份唯一職責；判斷現況以前兩份為準）

| 檔案 | 職責 | 什麼時候動它 |
|------|------|------------|
| `todo.md` | 待辦任務清單 | 完成任務打勾；新任務加進去 |
| `PROJECT.md` | 專案脈絡：架構、已完成、決策、真實/mock 對照、慣例與踩坑 | 完成一件事改寫對應段落（只留最終狀態，不寫流水帳） |
| `plan.md` | 未來 Phase 藍圖與投資決策框架 | 開新 Phase 時參考；Phase 完成後把該段成果移入 PROJECT.md |
| `docs/taiwan-market-notes.md` | 台股領域速查 | 幾乎不動 |

與其他文件衝突時，todo.md + PROJECT.md 是現況，其他是過時的。
（2026-07-05 整併：milestone.md、docs/thinking.md、docs/decisions.md、docs/tools.md、ui_plan.md 已併入 PROJECT.md 後刪除，歷史在 git。）

## 工作規範

- **push 一律等使用者明確說「push」才動**，commit 完不要自動 push
- README.md（英文）與 README.zh-TW.md（繁中）必須同步更新，更新後 commit（本機）
- plan.md / todo.md / CLAUDE.md 維持中文
- 只記錄影響架構或未來會忘記原因的決策；日常維護不寫進文件
- 個人工作制度（以下路徑是屋主本機的個人設定，clone 這個 repo 的其他人不會有這些檔案，**不存在就整段忽略**）：
  - 大量讀取、掃 repo、批次改檔 → 先讀 `~/.claude/rules/dispatch.md` 再派 subagent
  - 拿不準「算不算完成」「要不要問使用者」 → 讀 `~/.claude/rules/judgment.md`
  - 新 session 接手長期工作 → 讀 `.claude/rules/letter.md`（本專案交接信，gitignored）

## 當前狀態

Dashboard 建皮完成；下一階段是自建計算層（指標→評分→優化）。隊友 branch 只涵蓋回測，merge 時核對清單見 todo.md。現況細節一律看 todo.md + PROJECT.md，不在這裡重複。
