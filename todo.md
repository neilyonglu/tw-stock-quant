# Dashboard 建皮 Todo

目標：先把三個頁面的介面框架建起來，資料暫時用 yfinance 的台股代碼（如 `2330.TW`）塞假資料，
之後 Phase 1 資料管線完成後再換成 twstock + FinMind。

技術選型：
- 前端：Next.js 15（App Router）+ Tailwind CSS + shadcn/ui + TradingView lightweight-charts
- 後端：FastAPI（之後接 Phase 1 資料管線）
- 部署：Vercel（前端）+ Railway 或 Render（後端）

設計參考：
- 整體風格：Robinhood（消費者友善，結論優先，一般大眾看得懂）
- 視覺語言：Linear（深色主題、排版層次乾淨）
- 圖表空間：TradingView（側欄 + 主圖 + 子圖配置）

---

## Step 0 — 建立 Next.js 專案

- [x] 在專案根目錄下建立 `frontend/` 資料夾
- [x] 初始化 Next.js 15：
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --app
  ```
- [x] 安裝套件：
  ```bash
  cd frontend
  npx shadcn@latest init
  npm install lightweight-charts lightweight-charts-react-components
  ```
  ```bash
  # Python 端（專案根目錄）
  uv add yfinance
  ```
- [x] 驗證：`npm run dev`，localhost:3000 能開啟

---

## Step 1 — 建立 app 框架（多頁面結構）

Next.js App Router 資料夾結構：

```
frontend/src/app/
├── layout.tsx                  # 全域 layout，含 sidebar 導航
├── page.tsx                    # 首頁 → redirect 到 /market
├── market/
│   └── page.tsx                # 頁面一：市場總覽
├── stock/
│   └── [ticker]/
│       └── page.tsx            # 頁面二：個股 K 線分析
└── screening/
    └── page.tsx                # 頁面三：每週選股結果

frontend/src/components/
├── sidebar.tsx                 # 側欄導航元件
├── charts/
│   └── kline-chart.tsx         # 可重用 K 線圖（TradingView lightweight-charts）
└── ui/                         # shadcn/ui 自動產生的元件
```

- [x] 建立上述資料夾和空白 page.tsx
- [x] `layout.tsx` 寫好 sidebar，包含：
  - 專案名稱（台股分析）
  - 三頁導航連結
  - 底部「最後更新時間」
- [x] sidebar 深色主題（`bg-zinc-900`），高亮當前頁
- [x] 確認 `npm run dev` 可以跑起來，三個頁面都能切換

---

## Step 2 — 頁面二先做：個股 K 線分析（最核心的畫面）

> 先做頁面二是因為它用到最漂亮的圖表元件，建好後整體風格就定了。

K 線圖使用 `lightweight-charts`，參考 TradingView 官方 npm 套件的 React 用法。

參考來源（不一定要照做，但可以對照）：
- 圖表設定：https://github.com/locupleto/streamlit-lightweight-charts-v5 的 `chart_demo.py`
  — 底層同為 TradingView lightweight-charts，五層疊圖、子圖高度、指標顏色的設定邏輯可直接對照
- 台股選股邏輯：https://github.com/kevin801221/stock-strategies-only

- [x] `frontend/src/app/stock/[ticker]/page.tsx`
- [x] sidebar（頁面內側欄）加一個輸入框：股票代碼（預設 `2330`）
- [x] 時間區間選擇：1 個月 / 3 個月 / 6 個月 / 1 年（shadcn/ui `ToggleGroup`）
- [x] 用 yfinance API（Route Handler + python3 subprocess）抓資料，轉成 OHLCV 格式
- [x] `kline-chart.tsx` 建五層疊圖：
  - 主圖：K 線 + SMA20（橘）+ SMA60（藍）
  - 子圖 1：成交量（Volume）
  - 子圖 2：RSI（14）
  - 子圖 3：MACD
- [x] 主圖高度 500px，每個子圖 120px
- [x] 主圖下方用 shadcn/ui `Card` 顯示速查資訊（4 欄）：
  - 現價 / 漲跌幅
  - RSI 數值 + 狀態（超買 / 健康 / 超賣），加顏色 badge
  - MACD 狀態（金叉 / 死叉）
  - 成交量 vs 5 日均量比值
- [x] 每個指標旁邊一句白話說明（對一般大眾）

**追加（2026-06-30）**：
- [x] 標題列代碼旁顯示公司名稱（twstock 本地查表）
- [x] K 線圖／速查指標拆成 Tabs，速查 Card 移到第二分頁
- [x] K 線週期擴充：5分/15分/30分/60分/日/週/月（分鐘線固定時間區間，日/週/月可選）
- [x] 十字準心改 Magnet 模式、修正分鐘線時間軸時區 bug（詳見 docs/thinking.md）

---

## Step 3 — 頁面一：市場總覽 ✅ 完成（2026-06-30）

> 資料全部 mock，用固定數字填入，之後再接真實 API。

- [x] `frontend/src/app/market/page.tsx`
- [x] 頂部 4 個 `Card`（shadcn/ui）橫排：
  - 加權指數（mock：22,450 +1.2%）
  - 景氣燈號（mock：綠燈）
  - USD/TWD（mock：31.8）
  - 美債 10Y（mock：4.35%）
- [x] 三大法人區塊（3 欄）：
  - 外資今日：+85 億
  - 投信今日：+12 億
  - 自營商今日：-3 億
  - 每個欄位加一句白話說明（「外國大資金今天在買，是好訊號」）
- [x] 市場廣度區塊（5 欄）：漲家數 / 跌家數 / 平盤 / 漲停 / 跌停
- [x] 底部結論橫幅：「市場環境：多頭　建議操作強度：積極」（無 emoji，用顏色辨識）
- [x] 加重新整理按鈕（重抓 `/api/market`，目前後面接的還是同一份 mock）

**架構**：資料形狀定義在 `frontend/src/lib/types.ts`（`MarketOverviewData`），就是未來真正後端 API 的合約；`frontend/src/lib/mock-data.ts` 放假資料；`/api/market` Route Handler 回傳。Phase 9 接真後端時只改 Route Handler 內部，前端元件不用動（詳見 docs/thinking.md 十四）。

**已知待辦（留給 Step 5）**：手機寬度（375px）目前會橫向溢出，因為 Sidebar 響應式收合還沒做，個股分析頁也是同樣狀況，等 Step 5 一起處理。

---

## 對照看盤平台補齊功能（2026-06-30）

> 對照 Yahoo奇摩股市／Goodinfo／CMoney／HiStock 盤點出的缺口，全部先把介面做出來。
> 能拿到真資料的（yfinance／twstock，免金鑰）直接接真的；拿不到的先 mock，但型別
> 合約先定好（`lib/types.ts`），Phase 4/5/6 後端做完只要換 route handler 內部。
> 完整真實／mock 對照表＋為什麼這樣分，見 docs/thinking.md 十八～二十一。

### 個股分析頁新增

- [x] 分時走勢圖（真實，今日 1 分鐘 K）
- [x] 漲跌停價顯示（真實計算）
- [x] K 線型態辨識（mock——TA-Lib 沒裝在 route handler 用的 python 環境，見 thinking.md 二十）
- [x] 基本面 Tab：本益比/股價淨值比/殖利率/市值/股本/產業別/上市櫃（真實，yfinance + twstock）、近 6 個月營收（mock，Phase 4）
- [x] 籌碼面 Tab：三大法人近 5 日、融資融券、千張大戶比例（mock，Phase 5）
- [x] 五檔報價 sidebar 小部件（真實，twstock.realtime）
- [x] 新聞 Tab（mock）

### 市場總覽頁新增

- [x] 大盤分時走勢圖（真實，加權指數今日 1 分鐘 K）
- [x] 櫃買指數（真實）
- [x] 國際指數：道瓊/那斯達克/日經/上證（真實）
- [x] 台指期貨／外資未平倉（mock——plan.md 沒規劃期貨資料來源）
- [x] 排行榜 Tabs：類股漲跌幅／成交值／漲幅／跌幅（mock，需全市場掃描，Phase 1+6）
- [x] 新聞快訊（mock）

### 還沒做、不在這次範圍內

這些業界平台常見、但這次刻意沒做的功能（避免無限擴大範圍）：
- [ ] 同類股/概念股關聯比較
- [ ] 注意股/處置股清單
- [ ] 個股社群討論/投票功能（Yahoo「多空指標」類型）
- [ ] 警示燈號/警示股標記

---

## Step 4 — 頁面三：每週選股結果

> 資料全部 mock，確認表格排版和互動正確。

- [ ] `frontend/src/app/screening/page.tsx`
- [ ] 頂部：最後更新時間 + 市場環境 badge
- [ ] 主要表格（shadcn/ui `DataTable`）：
  - 欄位：排名 / 股票 / 評分 / 推薦理由（白話三層摘要）/ 進場價 / 停損 / 配置 %
  - 至少放 5 筆 mock 資料
  - 點欄位標題可排序
  - 點股票代碼跳轉到 `/stock/[ticker]`
- [ ] 表格右側放投組配置圓餅圖（用 Recharts pie chart，mock 數字）
- [ ] 底部 `下載 CSV` 按鈕（之後再接真實資料）

---

## Step 5 — 收尾細節

- [ ] 統一深色主題（`dark` class 加到 `html` 標籤）
- [ ] `layout.tsx` 加 metadata（`title: "台股分析"、description`）
- [ ] 確認三個頁面在手機尺寸（375px）下都能正常操作
- [ ] 驗收：三頁都能切換，K 線可以縮放 hover，選股表可點擊跳轉

---

## Step 6 — 排程：GitHub Actions

> 排程跑在 GitHub 雲端，每週五收盤後自動執行，電腦關著也沒問題，完全免費。

### 建立 workflow 檔案

```
.github/
└── workflows/
    ├── weekly_scan.yml      # 每週五 14:00 跑選股（台灣時間）
    └── premarket.yml        # 每週一至五 08:00 跑盤前快報（選配）
```

- [ ] 建立 `.github/workflows/` 資料夾
- [ ] 寫 `weekly_scan.yml`：

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

- [ ] 在 GitHub repo **Settings → Secrets → Actions** 新增三個 secret：
  - `FINMIND_TOKEN`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
- [ ] `main.py` 確認能單獨跑完整個選股流程並推播 Telegram
- [ ] 驗收：在 GitHub Actions 頁面手動觸發，確認跑成功

### APScheduler 的處置

- [ ] `src/alerts/scheduler.py` 保留，改成本機開發測試用途
- [ ] plan.md 備註：正式排程用 GitHub Actions，APScheduler 僅本機測試

---

## 建皮完成後的下一步（不在本次 todo）

建皮完成 = 介面框架就緒，但資料是假的。
下一步是 **Phase 1 資料管線**：
- `src/data/fetcher.py`：twstock 抓歷史 K 線
- `src/data/store.py`：Parquet 快取
- `src/api/main.py`：FastAPI 包裝 Python 分析結果，供前端呼叫
- 完成後把前端的 mock 資料換成真實 API 呼叫
