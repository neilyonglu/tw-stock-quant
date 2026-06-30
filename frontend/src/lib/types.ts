// 這份檔案是 Dashboard 所有 API 的合約，也是未來真正後端要回傳的形狀。
// Phase 9 換成真正後端時，只要回傳形狀符合這裡的定義，前端元件完全不用改。
// 詳見 docs/thinking.md 十四、十五。
//
// 每個 interface 上方都標註資料來源：
//   [真實]  現在就是真資料（yfinance / twstock，免金鑰，建皮期間直接接）
//   [mock]  現在是假資料，要等 Phase 1/4/5/6 的後端模組做完才能換真的，見各欄位後的對應 Phase

import type { Time } from "lightweight-charts"

// ─── /api/market ──────────────────────────────────────────────────────────────
// [mock] 景氣燈號、三大法人、市場廣度、環境結論——分別要等 Phase 1（資料管線）、
// Phase 5（FinMind 籌碼+總體）才有真資料。加權指數/櫃買指數已搬到 /api/market/indices（真實）。

export type MarketEnvironment = "多頭" | "盤整" | "空頭"
export type OperationIntensity = "積極" | "中性" | "保守"

// 台灣景氣對策信號燈：紅燈過熱 / 黃紅燈轉熱 / 綠燈穩定 / 黃藍燈轉弱 / 藍燈衰退
export type BusinessCycleLight = "red" | "yellow-red" | "green" | "yellow-blue" | "blue"

export interface MarketOverviewData {
  updated_at: string // ISO 8601
  business_cycle: { light: BusinessCycleLight; label: string } // mock，Phase 5：data.gov.tw #6099
  usdtwd: { value: number; change: number } // mock，但其實 yfinance USDTWD=X 就能拿到真的，先沒接
  us10y: { value: number; change: number } // mock，但 yfinance ^TNX 也能拿到真的，先沒接
  // 三大法人今日買賣超，單位：億元
  institutional: { foreign: number; trust: number; dealer: number } // mock，Phase 5：FinMind
  breadth: { up: number; down: number; flat: number; limit_up: number; limit_down: number } // mock，Phase 5：TWSE OpenAPI
  // 上市加權成交值（億元）/ 成交量（億股），跟 breadth 同一個來源，mock，Phase 5：TWSE OpenAPI
  turnover: { value: number; volume: number }
  environment: { verdict: MarketEnvironment; intensity: OperationIntensity } // mock，Phase 5：macro/context.py
}

// ─── /api/market/indices ────────────────────────────────────────────────────────
// [真實] yfinance：^TWII（加權）、^TWOII（櫃買）、道瓊/那斯達克/日經/上證，免金鑰，現在就是真資料

export interface IndexQuote {
  value: number
  change: number
  change_pct: number
}

export interface GlobalIndex {
  name: string // 道瓊工業 / 那斯達克 / 日經225 / 上證指數
  value: number
  change_pct: number
}

export interface MarketIndicesData {
  taiex: IndexQuote // 加權指數（^TWII）
  otc: IndexQuote // 櫃買指數（^TWOII）
  global: GlobalIndex[]
}

// ─── /api/market/intraday、/api/stock/[ticker]/intraday ────────────────────────
// [真實] yfinance period=1d interval=1m，個股與大盤共用同一支 python 腳本

export interface IntradayPoint {
  time: number // unix timestamp（秒）
  price: number
  avg_price: number // 累計均價線
  volume: number
}

export interface IntradaySeries {
  prev_close: number // 用來畫平盤參考線
  points: IntradayPoint[]
}

// ─── /api/market/futures ────────────────────────────────────────────────────────
// [mock] 台指期、外資未平倉——plan.md 目前沒有規劃期貨資料來源，要另外找（如券商 API），先 mock

export interface FuturesData {
  tx_price: number // 台指期近月價格
  tx_change: number
  basis: number // 正逆價差（期貨 - 現貨）
  foreign_oi: number // 外資台指期淨未平倉口數，正＝偏多、負＝偏空
}

// ─── /api/market/rankings ───────────────────────────────────────────────────────
// [mock] 類股/成交量/漲跌幅排行——需要全市場掃描，Phase 1 資料管線 + Phase 6 排行邏輯做完才能換真的

export interface RankedItem {
  ticker?: string // 個股排行才有；類股排行沒有
  name: string
  value: number
  unit: string // "%"、"億元" 等
}

export interface MarketRankings {
  sector_performance: RankedItem[] // 類股漲跌幅排行
  volume_leaders: RankedItem[] // 成交值排行
  gainers: RankedItem[] // 漲幅排行
  losers: RankedItem[] // 跌幅排行
}

// ─── /api/market/news、/api/stock/[ticker]/news ─────────────────────────────────
// [mock] 個股與大盤新聞——Phase 6 規劃用 feedparser 收 TWSE 重大訊息 RSS，範圍限持倉股，
// 全市場新聞牆要另外找來源，先 mock

export interface NewsItem {
  time: string // ISO 8601
  title: string
  source: string
}

// ─── /api/stock/[ticker]?period=&interval= ─────────────────────────────────────
// 日/週/月 → time 是 "YYYY-MM-DD"；分鐘線（5m/15m/30m/60m）→ time 是 unix timestamp（秒）
// [真實] K 線/指標/漲跌停價 全部來自 yfinance + 公式計算；K 線型態辨識是 [mock]（見下方說明）

export interface Candle {
  time: Time
  open: number
  high: number
  low: number
  close: number
}

export interface VolumeBar {
  time: Time
  value: number
  color: string
}

export interface TimeValue {
  time: Time
  value: number
}

export interface MacdPayload {
  line: TimeValue[]
  signal: TimeValue[]
  histogram: TimeValue[]
}

export interface LatestMetrics {
  price: number
  change: number
  change_pct: number
  rsi: number
  macd_crossover: "golden" | "dead"
  volume_ratio: number
  limit_up: number // 漲停價，依前收盤 ±10% 估算
  limit_down: number // 跌停價，同上
}

// K 線型態（晨星、錘子線、吞噬等）。[mock]：TA-Lib 的 61 種型態辨識（pattern.py，Phase 2）
// 還沒接進這支 Dashboard 用的 python script（執行環境沒裝 TA-Lib C 函式庫），先用假資料佔位。
export interface CandlePattern {
  time: Time
  name: string
  signal: "bullish" | "bearish"
}

export interface StockData {
  ticker: string
  name: string
  candles: Candle[]
  volume: VolumeBar[]
  sma20: TimeValue[]
  sma60: TimeValue[]
  rsi: TimeValue[]
  macd: MacdPayload
  patterns: CandlePattern[] // mock，見上方說明
  latest: LatestMetrics
}

// ─── /api/stock/[ticker]/profile ────────────────────────────────────────────────
// [真實] 產業別/上市櫃別來自 twstock；本益比/股價淨值比/殖利率/市值/股本來自 yfinance .info
// [mock] 月營收——Phase 4：CasualMarket /financial/revenue

export interface MonthlyRevenue {
  month: string // YYYY-MM
  revenue: number // 億元
  yoy: number // 年增率 %
}

export interface StockProfile {
  industry: string // twstock group
  listed_market: "上市" | "上櫃"
  market_cap: number // 億元
  shares_outstanding: number // 億股
  pe_ratio: number | null
  pb_ratio: number | null
  dividend_yield: number | null // %
  eps: number | null // 每股盈餘（近 12 個月）
  week52_high: number | null
  week52_low: number | null
  analyst_target: number | null // 分析師平均目標價
  analyst_count: number | null // 提供目標價的分析師人數
  monthly_revenue: MonthlyRevenue[] // mock，近 6 個月
}

// ─── /api/stock/[ticker]/chip ───────────────────────────────────────────────────
// [mock] 個股層級籌碼面——Phase 5：FinMind TaiwanStockInstitutionalInvestorsBuySell /
// TaiwanStockMarginPurchaseShortSale / TaiwanStockShareholding（千張大戶）

export interface StockChipData {
  institutional: { date: string; foreign: number; trust: number; dealer: number }[] // 近 5 日，張數
  margin_balance: number // 融資餘額（張）
  margin_balance_change: number
  short_balance: number // 融券餘額（張）
  short_balance_change: number
  big_holder_ratio: number // 千張大戶持股比例 %
}

// ─── /api/stock/[ticker]/orderbook ──────────────────────────────────────────────
// [真實] twstock.realtime 直接拿 TWSE/TPEx 即時五檔，免金鑰。盤前/盤後可能沒有掛單，
// asks/bids 長度可能小於 5（甚至是空陣列），UI 要處理這個狀況

export interface OrderBookLevel {
  price: number
  volume: number // 張
}

export interface OrderBookData {
  asks: OrderBookLevel[] // 委賣，由低到高 5 檔
  bids: OrderBookLevel[] // 委買，由高到低 5 檔
}
