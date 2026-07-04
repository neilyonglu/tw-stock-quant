# 工具索引

> 從 CLAUDE.md 抽出（2026-07-04）。新增/更換工具時更新這裡，CLAUDE.md 不放工具細節。

## 資料來源

| 工具 | 用途 | 備註 |
|------|------|------|
| `twstock` | 台股日 K 線、即時報價 | PyPI 版本（2026-07-01 起，原本的 `~/proj/tools/twstock` editable fork 已刪除）；股票代碼表會過期，需要時手動跑 `twstock.codes.fetch.__update_codes()` 更新 |
| `CasualMarket` | 財報、月營收、股利（MCP Server） | 已設定，stdio 模式 |
| `finmind` | 三大法人、融資券、台指期、股東結構 | 免費帳號 600 req/hr |
| `yfinance` | USD/TWD 匯率（`USDTWD=X`）、美債（`^TNX`） | 免費 |
| `fredapi` | 美債、匯率備援 | 需 FRED_API_KEY |
| `feedparser` | TWSE 重大訊息 RSS | 免費 |
| TWSE OpenAPI | 漲跌家數、上市資料 | `requests` 直打 |
| data.gov.tw #6099 | 台灣景氣燈號 | `requests` 直打 |

## 分析 / 基礎設施

| 工具 | 用途 |
|------|------|
| `TA-Lib` | 150+ 技術指標、61 種 K 線型態（從 source 編譯；`make` 單執行緒，不加 `-j`） |
| `backtesting.py` | 策略回測（bokeh 視覺化） |
| `alphalens-reloaded` | 多因子分析（IC、IR） |
| `pyportfolioopt` | 投組優化（均值-方差、風險平價） |
| `statsmodels` / `scipy` | 事件研究自建（OLS + t 檢定） |
| `scikit-learn` | 因子驗證（Phase 7+ 再啟用） |
| `pyarrow` | Parquet 快取讀寫 |
| `apscheduler` | 定時排程（每週五收盤後） |
| `python-telegram-bot` | 推播通知 |
| `plotly` | K 線圖 + 指標疊加 |
| `pytrends` | Google Trends 熱度訊號 |
