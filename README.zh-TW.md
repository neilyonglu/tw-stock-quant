# tw-stock-quant

繁體中文 | [English](README.md)

台灣股市（上市 / 上櫃）個人量化分析系統。涵蓋完整流程：資料擷取、技術指標、多因子選股、投組優化、定時排程、Telegram 推播 — 全程自建，不依賴付費黑盒子。

> **免責聲明**：本專案僅供個人學習與研究，不構成任何投資建議。

---

## 功能

- **技術分析**：TA-Lib（150+ 指標、61 種 K 線型態）
- **策略回測**：`backtesting.py`，含夏普比率、最大回撤、勝率報告
- **基本面篩選**：Piotroski F-Score、FCF 轉換率、月營收年增率
- **籌碼面**：外資、投信、自營商、融資融券（FinMind）
- **多因子評分**：總體 → 基本面 → 籌碼 → 技術，四層框架
- **投組優化**：`pyportfolioopt`（均值-方差、風險平價）
- **自動排程**：每週五收盤後自動執行
- **推播通知**：Telegram Bot

---

## 安裝

```bash
git clone https://github.com/neilyonglu/tw-stock-quant.git
cd tw-stock-quant
uv sync
```

複製 `.env.example` 為 `.env` 並填入 API key（均為選填，系統會自動 fallback 至免費替代來源）。

---

## Dashboard

以 **Next.js 16 + Tailwind v4 + shadcn/ui + TradingView lightweight-charts** 建立的網頁分析介面，搭配 Python 資料層。

| 步驟 | 頁面 | 狀態 |
|------|------|------|
| 0 | 專案初始化（Next.js + shadcn + lightweight-charts） | ✅ 完成 |
| 1 | app 框架（側欄 + 三頁路由） | ✅ 完成 |
| 2 | 個股分析頁 — 五層 K 線圖（SMA 趨勢圖例、高低點標記、成交量均線）、7 種時間週期、分時/基本面/籌碼面/五檔/新聞 Tabs（yfinance/twstock 拿得到的用真資料，拿不到的先 mock） | ✅ 完成 |
| 3 | 市場總覽頁 — 大盤/國際指數（真資料）、三大法人/市場廣度/排行榜/期貨/新聞（mock，待 Phase 1/4/5/6 後端） | ✅ 完成 |
| 4 | 每週選股結果頁 — 可排序表格、投組配置圓餅圖、CSV 下載（mock 資料） | ✅ 完成 |
| 5 | 收尾細節 — 深色主題寫死（拿掉 `next-themes`，本來就沒有亮色 variant）、Sidebar 響應式（手機底部 nav／平板 icon bar／桌面完整版）、375px 版面修正、圖表縮放下限（不能縮出資料範圍外）、日期時間格式統一成 `zh-TW`、紅漲綠跌色彩審查 | ✅ 完成 |

完整的「哪些欄位是真資料、哪些是 mock」對照表，見 [docs/thinking.md](docs/thinking.md)。

### 架構：中台 / 前端 / 後端

抓資料的工作獨立成一個**中台**（`data_service/`，FastAPI，記憶體 TTL 快取）——前端（顯示）和後端（計算，另開 branch 開發、之後 merge 回 main）都跟中台要 raw 資料，不各自打外部 API。API contract 見 [data_service/README.md](data_service/README.md)。

本機開發中台跟前端要同時跑起來。`./scripts/dev.sh` 一個指令同時啟動兩個（Ctrl+C 會兩個一起關掉）；或分開手動啟動：

```bash
uv run uvicorn data_service.main:app --reload --port 8001   # 中台
cd frontend && npm run dev                                   # 前端
```

---

## 開發路線

| 階段 | 說明 | 狀態 |
|------|------|------|
| 0 | 環境建置 | ✅ 完成 |
| 1 | 資料管線（twstock → Parquet） | 待開始 |
| 2 | 技術指標（TA-Lib 封裝） | 待開始 |
| 3 | 策略回測（backtesting.py） | 待開始 |
| 4 | 基本面整合（CasualMarket） | 待開始 |
| 5 | 籌碼面 + 總體環境（FinMind） | 待開始 |
| 6 | 選股系統 + 投組優化 + 排程推播 | 待開始 |
| 7 | 因子驗證 + 事件研究 | 待開始 |
| 8 | 情緒面（Google Trends / pytrends） | 待開始 |
| 9 | Dashboard API 遷移（FastAPI） | 待開始 |

---

## 資料來源

| 工具 | 用途 |
|------|------|
| [twstock](https://github.com/mlouielu/twstock) | 台股歷史 OHLCV、即時報價 |
| [FinMind](https://finmind.github.io/) | 三大法人、融資券、財務報表 |
| [CasualMarket](https://github.com/sacahan/CasualMarket) | 財報、月營收、股利（MCP Server） |
| TWSE OpenAPI | 漲跌家數、官方行情 |
| yfinance | USD/TWD 匯率、美債殖利率 |
| data.gov.tw | 台灣景氣燈號 |

---

## 參考來源

- [locupleto/streamlit-lightweight-charts-v5](https://github.com/locupleto/streamlit-lightweight-charts-v5) (MIT)
- [kevin801221/stock-strategies-only](https://github.com/kevin801221/stock-strategies-only) (MIT)

---

## 授權

[MIT](LICENSE)
