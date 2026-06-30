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

---

## 2026-06-30 — Dashboard Step 2 微調

### 十二、多時間週期（分鐘/日/週/月）

K 線週期從原本固定日線，擴充成 5/15/30/60 分鐘 + 日/週/月，共 7 檔。yfinance 對短週期有資料範圍限制（5–60 分線僅近 60 天、1 分線僅近 7 天），所以分鐘線不開放使用者選時間區間，固定用一個夠用的區間（如 5 分線固定抓 5 天）。日/週/月則保留時間區間選擇（如 6M/1Y、1Y/2Y/5Y、5Y/10Y/全部）。

`get_stock_data.py` 新增 `interval` 參數（第三個 CLI 參數），`route.ts` 對應多傳一個 query string。

### 十三、lightweight-charts 分鐘線時間軸是 UTC，不是瀏覽器本地時區

lightweight-charts 的時間軸刻度一律用 **UTC** 計算與顯示，跟瀏覽器或系統時區無關。一開始把台北時間（`yfinance` 回傳的 tz-aware Asia/Taipei timestamp）直接轉成真正的 UTC epoch（`ts.timestamp()`），結果台股開盤 09:00 顯示成 01:00，整條時間軸都位移了 8 小時。

**解法**：用「假 UTC」技巧——取 timestamp 的「本地壁鐘時間」欄位（年月日時分秒，不做時區轉換），當成 UTC 去算 epoch：

```python
import calendar
calendar.timegm(ts.timetuple())  # ts 是 tz-aware 的 Asia/Taipei Timestamp
```

`ts.timetuple()` 回傳的是 `ts` 自身時區的壁鐘時間欄位（不轉換成 UTC），`calendar.timegm()` 再把這組欄位當 UTC 算 epoch。兩者疊加後，lightweight-charts 用 UTC 規則顯示出來的數字，正好等於台北壁鐘時間。日/週/月線本來就用日期字串（`YYYY-MM-DD`），不受影響。

### 十四、API 介面設計原則（為了之後接後端）

建皮期間所有資料都還是 yfinance（個股頁）或 mock（市場總覽頁），但 **Phase 9 之後會換成真正的後端**（twstock + FinMind + CasualMarket，包成 FastAPI 或繼續用 Next.js Route Handler）。為了讓那次替換只動資料層、不動畫面元件，目前統一遵守：

1. **前端元件永遠透過 `fetch('/api/...')` 拿資料，不直接 import mock 物件或呼叫 Python**。換句話說，畫面元件（`*-view.tsx`）只認得 Route Handler 回傳的 JSON 形狀，不管背後是 subprocess、mock，還是真後端。
2. **Route Handler 的 JSON 形狀，就是未來後端 API 的合約**——現在改的話兩邊都要改，所以設計時要先想清楚欄位是「最終想要的樣子」，不要為了方便先抓而抓。例如 `get_stock_data.py` 回傳 `name` 欄位，是因為個股頁最終一定要顯示公司名稱，不是因為 yfinance 剛好有。
3. Phase 9 遷移時，只需要把 Route Handler 內部從「spawn python3 subprocess / 回傳 mock」換成「打真正的後端 API 或直接查資料庫」，**回傳的 JSON 形狀不變**，前端元件完全不用動。

---

## 2026-06-30 — Dashboard Step 3 完成

### 十五、市場總覽頁實際套用「型別合約」模式

延續十四的原則，第一次具體實作：

- `frontend/src/lib/types.ts`：`MarketOverviewData` interface，欄位是「最終想要的樣子」（加權指數、景氣燈號、USD/TWD、美債 10Y、三大法人、市場廣度、環境結論），不是 yfinance/mock 剛好有什麼就放什麼
- `frontend/src/lib/mock-data.ts`：唯一的假資料來源，型別套用 `MarketOverviewData`
- `frontend/src/app/api/market/route.ts`：唯一的資料入口，現在回傳 mock，Phase 9 換成 `macro/context.py`（市場環境判斷）+ `chip.py`（三大法人）算出來的真資料即可，**形狀不變**
- `market-overview-view.tsx` 只認 `fetch('/api/market')` 回來的 JSON，不 import mock 物件

之後 Step 4（選股結果頁）比照同一套模式：先定 `ScreeningResult` 型別、`mock-data.ts` 加假資料、`/api/screening` route 回傳。

---

## 2026-06-30 — 修正漲跌顏色：紅漲綠跌（台股慣例）

### 十六、不要用美股的 green-up / red-down

一開始所有漲跌相關顏色（K 線、成交量、MACD 柱狀圖、股價漲跌文字、加權指數、三大法人買賣超、多頭/空頭橫幅、技術訊號 SignalBadge）都沿用 `ui_plan.md` 抄 TradingView 預設配色（漲=teal #26A69A、跌=red #EF5350），這是美股慣例。**台股／中港日韓慣例是紅漲綠跌**，跟美股相反，必須改掉。

修正範圍（只動「代表漲跌方向」的顏色，不動 RSI 超買超賣門檻線、景氣燈號 5 色階、amber 警示色這些非方向性的顏色）：

| 檔案 | 內容 |
|------|------|
| `src/api/get_stock_data.py` | 成交量柱顏色（`STOCK_UP`/`STOCK_DOWN` 常數） |
| `frontend/src/components/charts/kline-chart.tsx` | K 線 upColor/downColor/wick/border、MACD 柱狀圖正負色 |
| `frontend/src/components/stock-analysis-view.tsx` | 現價/漲跌文字與 Card 顏色 |
| `frontend/src/components/market-overview-view.tsx` | 加權指數、三大法人買賣超顏色（USD/TWD、美債 10Y 維持原樣——這兩個本來就是「數字變大＝紅」，方向沒錯）|
| `frontend/src/components/market-banner.tsx` | 多頭＝紅、空頭＝綠 |
| `frontend/src/components/signal-badge.tsx` | positive（站上均線/金叉）＝紅、negative（跌破均線/死叉）＝綠 |
| `frontend/src/app/globals.css` | `--stock-up`/`--stock-down` token 值對調（目前程式碼還沒用到這兩個 token，但先修正避免之後踩坑）|

兩處用「漲=紅」剛好就是邏輯正確、不用改的：USD/TWD 與美債 10Y 的顏色判斷本來就是「數字變大（change >= 0）→ 紅」，跟台股慣例的「數字變大＝紅」是同一條規則，只是程式裡原本的理由寫的是「對股市不利＝紅」，結果碰巧一致。

### 十七、API 型別合併到 lib/types.ts

順便把原本散在 `kline-chart.tsx`（`Candle`/`VolumeBar`/`TimeValue`/`MacdPayload`）和 `stock-analysis-view.tsx`（`StockData`/`LatestMetrics`）裡的型別，全部搬進 `frontend/src/lib/types.ts`，跟 `MarketOverviewData` 放一起，符合十四訂的原則：**Route Handler 的 JSON 形狀就是合約，要有單一定義來源**。`kline-chart.tsx` 改成從 `lib/types.ts` import 並重新 export，不影響既有 import 寫法。

---

## 2026-06-30 — 對照各大看盤平台補齊功能

### 十八、為什麼要做這次擴充

上完 Step 2、Step 3 後，對照 Yahoo奇摩股市、Goodinfo、CMoney、HiStock 等平台，盤點出我們缺的功能（個股：分時走勢圖、五檔報價、基本面數據、個股籌碼、新聞；大盤：分時走勢圖、櫃買指數、國際指數、台指期貨、排行榜、新聞快訊）。決定每一項都先把**介面長出來**，能拿到真資料的直接接真的，拿不到的用 mock 佔位但**型別合約先定好**，這樣 Phase 4/5/6 後端做完只要換 route handler 內部，畫面完全不用動（原則見十四）。

### 十九、真實 vs mock 的判斷標準

**判斷標準只有一個：yfinance（或 twstock 本地查表）能不能免金鑰直接拿到。能拿到的全部接真的，不因為「之後 Phase X 會有更好的資料」就先將就用 mock。**

實際測試結果（都用 yfinance，2026-06-30 測試於本機可正常取得）：

| 資料 | 真實／mock | 來源 |
|------|-----------|------|
| 加權指數、櫃買指數 | **真實** | yfinance `^TWII`、`^TWOII` |
| 國際指數（道瓊/那斯達克/日經/上證）| **真實** | yfinance `^DJI`/`^IXIC`/`^N225`/`000001.SS` |
| 個股／大盤分時走勢（今日 1 分鐘 K）| **真實** | yfinance `period=1d interval=1m`，個股傳 `{ticker}.TW`、大盤傳 `^TWII` |
| 個股本益比/股價淨值比/殖利率/市值/股本 | **真實** | yfinance `Ticker.info`（`trailingPE`/`priceToBook`/`dividendYield`/`marketCap`/`sharesOutstanding`）|
| 個股產業別、上市／上櫃別 | **真實** | twstock 本地查表（`twstock.codes[ticker].group`/`.market`），不用打 API |
| 個股漲跌停價 | **真實計算** | 前收盤 ±10%，依 TWSE 跳動單位取整（`_tick_size`），不是外部資料但是真公式 |
| USD/TWD、美債 10Y | mock（但其實也能真，故意先留著）| `mock-data.ts`，理由見下方 |
| 景氣燈號、市場廣度（漲跌家數）、三大法人（大盤層級）、市場環境結論 | mock | 等 Phase 1 資料管線 + Phase 5 FinMind/data.gov.tw 做完 |
| 台指期貨、外資未平倉 | mock | plan.md 完全沒規劃資料來源，要另外找（券商 API） |
| 類股漲跌幅／成交量／漲跌幅排行榜 | mock | 需要全市場掃描，等 Phase 1 + Phase 6 |
| 個股層級三大法人、融資融券、千張大戶 | mock | Phase 5：FinMind |
| 個股月營收 | mock | Phase 4：CasualMarket `/financial/revenue` |
| 個股五檔報價（委買委賣盤口）| mock | yfinance 沒有 Level 1 資料，plan.md 沒規劃來源 |
| 個股／大盤新聞 | mock | Phase 6 的 feedparser 只收持倉股 TWSE 公告，全市場新聞牆要另外找來源 |
| K 線型態辨識（錘子線、吞噬等）| mock | TA-Lib 已裝在 `~/proj/stock_analysis/.venv`，但 Route Handler 是用系統 `python3`（miniconda），沒裝 TA-Lib，兩個環境不一樣，這次先不處理 |

**故意留 mock 的兩個例外**：USD/TWD 和美債 10Y 其實 yfinance 也拿得到（`USDTWD=X`、`^TNX`），這次沒接是因為它們已經在 `/api/market` 的既有合約裡跑得好好的，不想為了「順便」而動到已驗證過的程式碼路徑，之後跟景氣燈號等其他 `/api/market` 欄位一起換成真資料即可。

### 二十、route handler 內部執行的 python 解譯器跟 uv venv 是兩回事

`route.ts` 一律用 `execFile("python3", ...)`，這支 `python3` 是系統 PATH 找到的（這台機器上是 miniconda 的，不是 `~/proj/stock_analysis/.venv`）。yfinance、twstock 剛好兩邊都有裝，但 TA-Lib **只**裝在 uv venv，所以 Dashboard 的 python script 目前不能用 TA-Lib。之後要嘛把 TA-Lib 也裝進這支 `python3` 的環境，要嘛把 `run-python.ts` 改成呼叫 uv venv 的 python（`uv run python3 ...`），兩者都還沒做，K 線型態先維持 mock。

### 二十一、新增檔案總覽

**Python（`src/api/`）**：
- `get_market_indices.py`：大盤＋國際指數（真實）
- `get_intraday.py <symbol>`：分時走勢，個股／大盤共用（真實）
- `get_stock_profile.py <ticker>`：個股基本資料（真實＋月營收 mock）
- `get_stock_data.py`：加 `limit_up`/`limit_down`（真實計算）、`patterns`（mock）

**前端共用**：
- `lib/run-python.ts`：抽出 `execFile` 共用邏輯，所有「真實」route 都呼叫這支
- `lib/types.ts`：每個 interface 上方都標註「[真實]/[mock]」＋資料來源，之後要查任何欄位現在是不是真的，直接看這支檔案最快
- `lib/mock-data.ts`：新增 `mockFuturesData`、`mockMarketRankings`、`mockMarketNews`、`mockStockChip()`、`mockOrderBook()`、`mockStockNews()`

**個股頁新元件**（`components/stock/`）：`order-book.tsx`（五檔，sidebar）、`intraday-tab.tsx`、`profile-tab.tsx`、`chip-tab.tsx`、`news-tab.tsx`。個股頁 Tabs 從 2 個（K 線圖／速查指標）擴成 6 個：分時／K 線圖／速查指標／籌碼面／基本面／新聞。

**市場頁新元件**（`components/market/`）：`intraday-section.tsx`、`global-indices-row.tsx`、`futures-card.tsx`、`rankings-section.tsx`（內嵌 Tabs：類股／成交值／漲幅／跌幅）、`news-section.tsx`。

**共用**：`components/charts/intraday-chart.tsx`（分時走勢圖，AreaSeries + 均價線 + 平盤參考線 + 成交量，個股／大盤共用）、`components/news-list.tsx`（新聞清單，個股／大盤共用）。

**新增 route**（10 個）：`/api/market/{indices,intraday,futures,rankings,news}`、`/api/stock/[ticker]/{profile,intraday,chip,orderbook,news}`。

`autoSize: true` 讓 chart 自動填滿容器寬度（高度仍需手動設定）。
