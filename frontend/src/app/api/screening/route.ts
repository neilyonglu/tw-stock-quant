import { mockScreeningData } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// 建皮期間直接回傳 mock。選股評分/投組配置是後端（隊友開發中）的計算工作，跟中台無關；
// 後端做完後只需要改這裡的實作，回傳形狀（ScreeningData）不變，前端元件不用動。
export async function GET() {
  return Response.json(mockScreeningData)
}
