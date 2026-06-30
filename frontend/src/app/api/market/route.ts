import { mockMarketData } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// 建皮期間直接回傳 mock。Phase 9 換成真正後端（macro/context.py 算市場環境、
// chip.py 抓三大法人）時，只需要改這裡的實作，回傳形狀（MarketOverviewData）
// 不變，前端元件不用動。
export async function GET() {
  return Response.json(mockMarketData)
}
