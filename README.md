# 台股分析系統

個人台灣股市量化分析工具。從資料抓取、技術指標、策略回測，到多因子選股、投組優化、Telegram 推播，全流程自建、完全自控。

> 免責聲明：本專案僅供個人學習與研究用途，不構成任何投資建議。

---

## 功能規劃

- **看盤 Dashboard**：Streamlit + TradingView 等級 K 線（streamlit-lightweight-charts-v5）
- **技術指標**：TA-Lib 150+ 指標，含 61 種 K 線型態識別
- **策略回測**：backtesting.py，含 Sharpe、最大回撤、勝率分析
- **基本面篩選**：Piotroski F-score、FCF 轉換率、月營收 YoY
- **籌碼面分析**：三大法人、融資券（FinMind）
- **多因子評分**：技術 × 基本面 × 籌碼 × 總體環境四層加權
- **投組優化**：pyportfolioopt（均值-方差、風險平價）
- **自動排程**：GitHub Actions，每週五收盤後自動執行
- **推播通知**：Telegram Bot

---

## 安裝

本專案使用 [uv](https://docs.astral.sh/uv/) 管理套件環境。

```bash
git clone https://github.com/neilyonglu/tw-stock-quant.git
cd stock_analysis
uv sync
```

### 環境變數（選填）

```bash
cp .env.example .env
# 編輯 .env，填入需要的 API key
```

詳見 [.env.example](.env.example)，所有 key 都是選填，系統會使用免費替代方案。

---

## 啟動 Dashboard

```bash
streamlit run src/dashboard/app.py
```

瀏覽器開啟 `http://localhost:8501`。

---

## 開發路線

詳見 [plan.md](plan.md)。

| Phase | 內容 | 狀態 |
|-------|------|------|
| 0 | 環境初始化、套件安裝 | ✅ 完成 |
| 1 | 資料管線（twstock → Parquet） | 進行中 |
| 2 | 技術指標模組（TA-Lib） | 待開始 |
| 3 | 策略回測（backtesting.py） | 待開始 |
| 4 | 基本面整合（CasualMarket） | 待開始 |
| 5 | 籌碼面 + 總體環境（FinMind） | 待開始 |
| 6 | 選股系統 + 投組優化 + 排程推播 | 待開始 |
| 7 | 因子驗證 + 事件研究 | 待開始 |
| 8 | 情緒面（Google Trends + Claude API） | 待開始 |
| 9 | Dashboard（Streamlit） | 進行中 |

---

## 資料來源

| 工具 | 用途 |
|------|------|
| [twstock](https://github.com/mlouielu/twstock) | 台股歷史 K 線、即時報價 |
| [FinMind](https://finmind.github.io/) | 三大法人、融資券、財務報表 |
| [CasualMarket](https://github.com/sacahan/CasualMarket) | 財報、月營收、股利（MCP Server）|
| TWSE OpenAPI | 市場廣度、官方行情 |
| yfinance | USD/TWD 匯率 |
| data.gov.tw | 景氣燈號 |

---

## 參考專案

- [locupleto/streamlit-lightweight-charts-v5](https://github.com/locupleto/streamlit-lightweight-charts-v5)（MIT）— Dashboard K 線元件
- [kevin801221/stock-strategies-only](https://github.com/kevin801221/stock-strategies-only)（MIT）— 台股選股邏輯與因子設計參考

---

## License

[MIT](LICENSE)
