// 這份檔案是 Dashboard 所有 API（/api/market、/api/stock/[ticker]）的合約，
// 也是未來真正後端要回傳的形狀。建皮期間資料來源是 mock 或 yfinance，
// Phase 9 換成真正後端時，只要回傳形狀符合這裡的定義，前端元件完全不用改。
// 詳見 docs/thinking.md 十四、十五。

import type { Time } from "lightweight-charts"

// ─── /api/market ──────────────────────────────────────────────────────────────

export type MarketEnvironment = "多頭" | "盤整" | "空頭"
export type OperationIntensity = "積極" | "中性" | "保守"

// 台灣景氣對策信號燈：紅燈過熱 / 黃紅燈轉熱 / 綠燈穩定 / 黃藍燈轉弱 / 藍燈衰退
export type BusinessCycleLight = "red" | "yellow-red" | "green" | "yellow-blue" | "blue"

export interface MarketOverviewData {
  updated_at: string // ISO 8601
  taiex: { value: number; change: number; change_pct: number }
  business_cycle: { light: BusinessCycleLight; label: string }
  usdtwd: { value: number; change: number }
  us10y: { value: number; change: number }
  // 三大法人今日買賣超，單位：億元
  institutional: { foreign: number; trust: number; dealer: number }
  breadth: { up: number; down: number; flat: number; limit_up: number; limit_down: number }
  environment: { verdict: MarketEnvironment; intensity: OperationIntensity }
}

// ─── /api/stock/[ticker]?period=&interval= ─────────────────────────────────────
// 日/週/月 → time 是 "YYYY-MM-DD"；分鐘線（5m/15m/30m/60m）→ time 是 unix timestamp（秒）

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
  latest: LatestMetrics
}
