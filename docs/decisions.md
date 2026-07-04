# 重要決策表

> 從 CLAUDE.md 抽出（2026-07-04）。只收「影響架構、或未來會忘記原因」的決策。完整推理過程在 docs/thinking.md 對應日期的章節。新決策：這裡加一行，thinking.md 寫脈絡。

| 決策 | 原因 |
|------|------|
| 不用 FinLab | 付費，要完全自控 |
| 推播用 Telegram Bot | `python-telegram-bot` |
| PTT 情緒分析用 pytrends | Google Trends 已足夠，不跑本地 NLP 模型 |
| 事件研究自建 | PyPI 無現成台股套件；`statsmodels` + `scipy.stats` 約 100 行 |
| TA-Lib 從 source 編譯 | apt 未收錄；`make` 單執行緒，不加 `-j` |
| 籌碼面用 FinMind | TWSE 官方 API 格式散，FinMind 整合好 |
| Dashboard 用 Next.js + FastAPI | 目標使用者是一般大眾，需支援手機、有視覺公信力；Streamlit 不符合 |
| 前端部署 Vercel，後端 Railway | 免費 tier 足夠；Next.js 在 Vercel 一鍵部署 |
| 建皮期間指標計算暫放 `src/api/get_stock_data.py` | 後端 merge 前的臨時計算佔位層；merge 後整支刪除，Route Handler 改打後端 API |
| shadcn 4.12 底層是 @base-ui/react（非 Radix UI） | ToggleGroup API 不同：value 是 string[]、active 用 aria-pressed:、無 type="single" |
| 資料中台獨立成 `data_service/`（FastAPI） | 前端＋後端都要跟外部來源要資料，各自抓會有 API 延遲＋重複邏輯；後端由隊友另開 branch 開發，中台需要穩定、有文件的 HTTP contract |
| 中台快取用記憶體 TTL cache，不是 Redis/SQLite | 先解決「完全沒快取」的核心問題；重啟清空、多實例不共享先接受，之後有需要再換 |
