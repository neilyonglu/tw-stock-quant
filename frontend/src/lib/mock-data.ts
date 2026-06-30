import type { MarketOverviewData } from "./types"

// 建皮期間用的假資料，形狀對齊 MarketOverviewData（見 types.ts 開頭說明）。
export const mockMarketData: MarketOverviewData = {
  updated_at: "2026-06-30T13:30:00+08:00",
  taiex: { value: 22450, change: 266, change_pct: 1.2 },
  business_cycle: { light: "green", label: "綠燈" },
  usdtwd: { value: 31.8, change: -0.3 },
  us10y: { value: 4.35, change: 0.02 },
  institutional: { foreign: 85, trust: 12, dealer: -3 },
  breadth: { up: 650, down: 280, flat: 120, limit_up: 23, limit_down: 2 },
  environment: { verdict: "多頭", intensity: "積極" },
}
