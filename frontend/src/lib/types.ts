// 這份型別就是「市場總覽」未來真正後端 API 的合約。
// 建皮期間 /api/market 回傳 mock 資料，Phase 9 換成真正後端（macro/context.py + chip.py）
// 時，只要回傳形狀符合這裡的定義，前端元件完全不用改。

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
