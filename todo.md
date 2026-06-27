# Dashboard 建皮 Todo

目標：先把三個頁面的介面框架建起來，資料暫時用 yfinance 的台股代碼（如 `2330.TW`）塞假資料，
之後 Phase 1 資料管線完成後再換成 twstock + FinMind。

參考來源：
- 圖表元件：https://github.com/locupleto/streamlit-lightweight-charts-v5
- 台股選股邏輯：https://github.com/kevin801221/stock-strategies-only

---

## Step 0 — 安裝套件

- [ ] `uv add streamlit`
- [ ] `uv add streamlit-lightweight-charts-v5`
- [ ] `uv add yfinance` （建皮期間的暫時資料源）
- [ ] 驗證：`streamlit run demo/chart_demo.py`（clone repo 後跑，確認圖表能出現）

---

## Step 1 — 建立 app 框架（多頁面結構）

Streamlit 多頁面用資料夾結構實現：

```
src/dashboard/
├── app.py                  # 主入口，定義 sidebar 導航
└── pages/
    ├── 1_market_overview.py
    ├── 2_stock_analysis.py
    └── 3_screening_results.py
```

- [ ] 建立上述資料夾和空白檔案
- [ ] `app.py` 寫好 sidebar，包含：
  - 專案名稱 / Logo 文字
  - 導航到三個頁面的連結
  - 底部顯示「最後更新時間」
- [ ] 確認 `streamlit run src/dashboard/app.py` 可以跑起來，三個頁面都能切換

---

## Step 2 — 頁面二先做：個股 K 線分析（最核心的畫面）

> 先做頁面二是因為它用到最漂亮的圖表元件，建好後就知道整體風格。

參考 `chart_demo.py` 的 `StockChart Demo` 段落。

- [ ] sidebar 加一個輸入框：股票代碼（預設 `2330`）
- [ ] sidebar 加時間區間選擇：1 個月 / 3 個月 / 6 個月 / 1 年
- [ ] 用 yfinance 抓資料：`yf.Ticker("2330.TW").history(period="6mo")`，轉成 `date/open/high/low/close/volume` 格式
- [ ] 用 `streamlit-lightweight-charts-v5` 建五層疊圖：
  - 主圖：K 線 + SMA20（橘）+ SMA60（藍）
  - 子圖 1：成交量（Volume）
  - 子圖 2：RSI（14）
  - 子圖 3：MACD
- [ ] 主圖高度 500px，每個子圖 120px
- [ ] 加 Dark / Light 主題切換（sidebar selectbox）
- [ ] 主圖下方用 Streamlit 的 `st.metric` 顯示速查資訊（4 個 column）：
  - 現價 / 漲跌幅
  - RSI 數值 + 狀態（超買/健康/超賣）
  - MACD 狀態（金叉/死叉）
  - 成交量 vs 5 日均量比值

---

## Step 3 — 頁面一：市場總覽

> 這頁資料全部 mock，用固定數字填入，之後再接真實 API。

- [ ] 頂部用 4 個 `st.metric` 橫排：
  - 加權指數（mock：22,450 +1.2%）
  - 景氣燈號（mock：🟢 綠燈）
  - USD/TWD（mock：31.8）
  - 美債 10Y（mock：4.35%）
- [ ] 三大法人區塊（mock 數字，用 `st.columns(3)`）：
  - 外資今日：+85 億
  - 投信今日：+12 億
  - 自營商今日：-3 億
- [ ] 市場廣度區塊（`st.columns(5)`）：
  - 漲家數 / 跌家數 / 平盤 / 漲停 / 跌停
- [ ] 底部一行文字：「市場環境：多頭 ✅  建議操作強度：積極」
- [ ] 整個頁面加 `st.button("重新整理")` 假裝可以更新（不接真實資料）

---

## Step 4 — 頁面三：每週選股結果

> 資料全部 mock，硬寫一個假的推薦清單，確認表格排版和互動正確。

- [ ] 頂部顯示：最後更新時間 + 市場環境 badge
- [ ] 主要表格（`st.dataframe`）：
  - 欄位：排名 / 股票 / 評分 / 推薦理由（三層摘要）/ 進場價 / 停損 / 配置 %
  - 至少放 5 筆 mock 資料
  - 加排序功能（點欄位標題）
- [ ] 表格右側放投組配置圓餅圖（用 plotly pie chart，mock 數字）
- [ ] 底部放 `st.download_button`，假裝能下載 CSV（先 pass，之後再接真資料）

---

## Step 5 — 收尾細節

- [ ] 整體 CSS 調整：用 `st.markdown` + `<style>` 把預設 Streamlit 上方留白縮小
- [ ] `app.py` 加 `st.set_page_config(layout="wide", page_title="台股分析系統", page_icon="📈")`
- [ ] 確認三個頁面在深色主題下都好看
- [ ] 驗收：`streamlit run src/dashboard/app.py`，三頁都能切換，頁面二的 K 線可以縮放 hover

---

---

## Step 6 — 排程：把 APScheduler 換成 GitHub Actions

> **為什麼換**：APScheduler 跑在本機，電腦要開著才能執行。
> GitHub Actions 跑在 GitHub 雲端，每週五 13:30 收盤後自動執行，電腦關著也沒問題，而且完全免費。
> 參考：kevin801221/stock-strategies-only 的 `.github/workflows/daily.yml`

### 建立 workflow 檔案

```
.github/
└── workflows/
    ├── weekly_scan.yml      # 每週五 14:00 跑選股（台灣時間）
    └── premarket.yml        # 每週一至五 08:00 跑盤前快報（選配）
```

- [ ] 建立 `.github/workflows/` 資料夾
- [ ] 寫 `weekly_scan.yml`，內容如下：

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

- [ ] 在 GitHub repo 的 **Settings → Secrets → Actions** 新增三個 secret：
  - `FINMIND_TOKEN`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
- [ ] `main.py` 確認能單獨跑完整個選股流程並推播 Telegram（建皮和資料管線都完成後才接）
- [ ] 驗收：在 GitHub Actions 頁面手動觸發 `workflow_dispatch`，確認跑成功

### APScheduler 的處置

- [ ] `src/alerts/scheduler.py` 保留但不刪，改成本機開發測試用途（手動跑）
- [ ] plan.md 備註：正式排程改用 GitHub Actions，APScheduler 僅本機測試用

---

## 建皮完成後的下一步（不在本次 todo）

建皮完成 = 介面框架就緒，但資料是假的。
下一步是 **Phase 1 資料管線**：
- `src/data/fetcher.py`：twstock 抓歷史 K 線
- `src/data/store.py`：Parquet 快取
- 完成後把頁面二的 yfinance 換成 twstock，頁面一接 TWSE OpenAPI
