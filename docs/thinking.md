# 台灣股市分析專案 — 決策日誌

記錄每個重要選擇的最終結論與原因。不記錄過程，只記錄「最終怎麼做」。

---

## 2026-06-27 — 工具鏈確立

### 一、核心工具

| 工具 | 角色 |
|------|------|
| `twstock` | 歷史 K 線、即時報價（台股專用） |
| `CasualMarket` | 財報、股利、月營收、外資（MCP Server） |
| `TA-Lib` | 技術指標計算 + 61 種 K 線型態 |
| `backtesting.py` | 策略回測框架 |

四個工具合起來覆蓋「資料 → 指標 → 策略 → 驗證」的完整流程，對個人台股投資者已足夠。

---

### 二、安裝方式

**TA-Lib**：PyPI 套件是 C 函式庫的 wrapper，需先從 source 編譯：

```bash
./configure --prefix=/usr && make && sudo make install && sudo ldconfig
uv add TA-Lib
```

注意：`make` 必須單執行緒，不加 `-j` 旗標。

**專案初始化**：
```bash
uv init --python 3.12
uv add backtesting TA-Lib
```

---

### 三、AI Skills 層

**選入的 8 個 skills**（來自 `equity-research` vertical）：

| Skill | 用途 | 對應階段 |
|-------|------|---------|
| `idea-generation` | 系統化選股篩選框架 | Phase 5 |
| `earnings-analysis` | 財報公布後快速分析 | Phase 4 |
| `earnings-preview` | 財報公布前設情境 | Phase 4 |
| `thesis-tracker` | 追蹤投資論點 | 貫穿全專案 |
| `catalyst-calendar` | 追蹤催化劑（財報日、除息、法說會） | Phase 5 |
| `morning-note` | 每日市場摘要 | Phase 6 |
| `model-update` | 新財報出來後更新估值 | Phase 4 |
| `sector-overview` | 選股前的產業大環境分析 | Phase 5 前置 |

存放位置：`.claude/skills/<skill-name>/SKILL.md`

**Dispatcher**：建立 `stock-analyst` skill 作為統一入口，路由邏輯：

```
財報後分析  →  earnings-analysis
財報前準備  →  earnings-preview
找新標的    →  idea-generation
追蹤持倉    →  thesis-tracker
找事件日期  →  catalyst-calendar
每日摘要    →  morning-note
更新數字    →  model-update
了解產業    →  sector-overview
```

---

## 2026-06-27 — 缺口分析與工具擴充

### 四、系統性缺口盤點

| 缺口 | 重要性 | 說明 |
|------|--------|------|
| 籌碼面（三大法人、融資券） | 🔴 高 | 台股主流投資人必看指標 |
| 總體經濟（景氣燈號、USD/TWD、美債）| 🔴 高 | 台灣出口導向，匯率與外資行為高度相關 |
| 財務健康評分（Piotroski、Altman Z）| 🟡 中 | 基本面篩選的量化底線 |
| 多因子框架（價值/動能/品質）| 🟡 中 | 學術實證最充分的選股方法 |
| 市場廣度（漲跌家數）| 🟡 中 | 判斷多頭是否有廣度 |
| 情緒/消息面 | 🟢 低 | Google Trends、PTT，屬輔助訊號 |
| 事件研究 | 🟢 低 | 量化法說會、除息等事件的前後報酬效應 |

**USD/TWD 特別重要**：台積電、聯發科收入以美元計價，USD/TWD 每動 1 元，台積電季 EPS 差約 0.3–0.5 元。此外，USD 走強時外資傾向撤出新興市場，匯率與台股外資行為高度相關。

---

### 五、各缺口工具選定

#### 籌碼面：FinMind

| 資料 | 資料集名稱 |
|------|-----------|
| 三大法人買賣超 | `TaiwanStockInstitutionalInvestorsBuySell` |
| 融資融券餘額 | `TaiwanStockMarginPurchaseShortSale` |
| 借券賣出 | `TaiwanStockSecuritiesLending` |
| 股東結構 | `TaiwanStockShareholding` |

免費版 600 req/hr，批次下載需付費。補充用 TWSE/TPEX OpenAPI（免費，`requests` 直打）。

#### 總體經濟

| 資料 | 工具 |
|------|------|
| 景氣燈號 | data.gov.tw dataset #6099（`requests`）|
| USD/TWD | `yfinance` ticker `USDTWD=X` |
| 美債 10Y | FRED `DGS10` via `fredapi` |
| 市場廣度 | TWSE OpenAPI |

台灣 PMI 無好的免費方案，暫不引入。

#### 財務健康評分

無現成台股套件。資料來源用 CasualMarket，計算邏輯自建於 `src/indicators/health.py`：
- Piotroski F-score（9 個財報指標 0/1 計分）
- FCF 轉換率（營業現金流 ÷ 淨利）
- Altman Z-score

#### 多因子框架

`alphalens-reloaded`：Quantopian 原版的維護 fork，用來分析因子 IC、IR，是最成熟的免費工具。

#### 情緒/消息面

- `pytrends`：Google Trends，有速率限制，批次查詢需節制
- PTT 情緒分析：爬蟲抓文章後送 Claude API 判斷，不在本地跑 NLP 模型

#### 排程與推播

- `APScheduler`：本機開發測試用途
- 正式排程：GitHub Actions（雲端，電腦關著也能跑）
- 推播：`python-telegram-bot`（Telegram Bot API）

#### 事件研究

自建於 `src/events/study.py`，使用 `statsmodels`（市場模型 OLS）+ `scipy.stats`（t 檢定），約 100 行。

#### 其他追加工具

- `pyportfolioopt`：投組優化（均值-方差、風險平價），決定候選股配置比例
- `feedparser`：解析 TWSE 重大訊息 RSS
- `scikit-learn`：因子非線性建模底層（Phase 7 後才用）

---

## 2026-06-28 — Dashboard 技術選型

### 六、前端框架選定：Next.js + FastAPI

**目標使用者**：公開給完全不懂股票的一般大眾，主要在手機上操作。

**選定技術棧**：

| 層 | 工具 | 部署 |
|---|---|---|
| 前端 | Next.js 15 + Tailwind CSS + shadcn/ui + TradingView lightweight-charts | Vercel（免費）|
| 後端 | FastAPI（包裝 Python 分析結果為 REST API） | Railway 或 Render（免費 tier）|
| 排程 | GitHub Actions | GitHub 雲端（免費）|

**shadcn/ui 選擇原因**：元件品質高，可完全客製化 source，深色主題原生支援。

**K 線圖**：TradingView `lightweight-charts` npm 套件，直接在 React 中整合，與 streamlit-lightweight-charts-v5 底層相同。

**設計參考**：
- **Robinhood**：整體消費者友善風格，結論優先
- **Linear**：視覺語言——深色主題、字體層次、卡片設計
- **TradingView**：K 線頁面空間配置（側欄 + 主圖 + 子圖）

**對一般大眾的設計原則**：
- 每個數字旁邊必須有一句白話說明（「外國大資金今天在買，是好訊號」）
- 三層資訊密度：首頁只給結論 → 個股頁給重要指標 → 進階頁給完整數據
- 手機版重新設計卡片式介面，不只是響應式縮小

### 七、UI/UX Skills 安裝

從 `github.com/nextlevelbuilder/ui-ux-pro-max-skill` 複製至 `~/.claude/skills/`：

- `ui-ux-pro-max`：設計決策層（50+ 風格、161 色盤、57 字體配對、99 條 UX 指南）
- `ui-styling`：實作層（shadcn/ui 元件指南、Tailwind 樣板、深色模式、手機版）

---

## 2026-06-28 — Dashboard Step 0 完成

### 八、實際安裝版本與注意事項

`create-next-app` 安裝的版本為 **Next.js 16.2.9**（非計畫中的 15），`frontend/AGENTS.md` 已有警告說明此版本有 breaking changes，開發時需參照 `node_modules/next/dist/docs/`。

**shadcn/ui 使用 Tailwind v4**：初始化後無 `tailwind.config.js`，改用 CSS 變數方式（`globals.css` 內直接定義設計 token）。shadcn/ui 元件安裝指令為 `npx shadcn@latest add <component>`。

**套件釐清**：`yfinance` 是 Python 套件，只能用 `uv add yfinance`，不能用 `npm install`。todo.md 原本寫錯，已修正。

**shadcn 版本差異**：ui_plan.md 以舊版 shadcn（HSL、`new-york` style）為設計參考，但實際安裝為 shadcn 4.12（Tailwind v4），使用 `oklch` 色彩格式與 `base-nova` style。設計意圖不變，實作改用 oklch 等價色值。`--radius: 0.25rem` 達到與 New York 相同的 sharp corner 效果。

**next-themes**：深色主題改用 `next-themes` ThemeProvider（`defaultTheme="dark"`），不 hardcode `className="dark"`，避免 SSR hydration mismatch。`html` 加 `suppressHydrationWarning`。

**字體**：Geist → Inter（Next.js `next/font/google`，`variable: "--font-sans"`）。

---

## 2026-06-28 — Dashboard Step 2 完成

### 九、建皮期間 API 層：Route Handler + python3 subprocess

原計畫後端用 FastAPI，但建皮階段還不需要獨立後端服務。改用 **Next.js Route Handler 直接 spawn python3 subprocess**，省去 FastAPI server 設定。

```
GET /api/stock/[ticker]?period=6mo
  → child_process.execFile('python3', [SCRIPT, ticker, period])
  → stdout JSON → Response.json(data)
```

Python 腳本路徑：`src/api/get_stock_data.py`，`process.cwd()` 在 Next.js 是 `frontend/`，所以腳本路徑為 `path.resolve(cwd, '..', 'src', 'api', 'get_stock_data.py')`。

Phase 9 再遷移至 FastAPI，屆時只需改 `fetch` 的 base URL。

### 十、@base-ui/react ToggleGroup API 與 shadcn 文件不同

shadcn 4.12 的 ToggleGroup 底層從 Radix UI 換成 **@base-ui/react**，API 有 breaking changes：

| 項目 | Radix UI（舊） | @base-ui/react（新） |
|------|--------------|---------------------|
| 單選模式 | `type="single"` | `multiple={false}`（預設即是） |
| value 型別 | `string` | `readonly string[]` |
| onValueChange 參數 | `string` | `string[]` |
| 選中樣式 | `data-[state=on]:` | `aria-pressed:` |

正確用法：
```tsx
<ToggleGroup
  value={[period]}
  onValueChange={(vals) => { if (vals.length > 0) setPeriod(vals[0]) }}
>
  <ToggleGroupItem value="6mo" className="aria-pressed:bg-zinc-700">
    6M
  </ToggleGroupItem>
</ToggleGroup>
```

### 十一、lightweight-charts v5 多 pane API

v5 原生支援 **單一 chart 實例 + 多 pane**，不需建立多個獨立 chart（crosshair 自動同步）：

```typescript
// 指定 pane index（第三參數）
chart.addSeries(CandlestickSeries, options, 0) // pane 0 主圖
chart.addSeries(HistogramSeries, options, 1)   // pane 1 成交量
chart.addSeries(LineSeries, options, 2)        // pane 2 RSI
chart.addSeries(LineSeries, options, 3)        // pane 3 MACD

// 設定各 pane 高度
chart.panes()[0].setHeight(500)
chart.panes()[1].setHeight(120)
```

`autoSize: true` 讓 chart 自動填滿容器寬度（高度仍需手動設定）。
