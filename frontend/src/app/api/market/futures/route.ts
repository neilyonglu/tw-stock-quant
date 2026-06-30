import { mockFuturesData } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// mock：台指期貨、外資未平倉，plan.md 目前沒有規劃資料來源（見 lib/types.ts FuturesData 說明）
export async function GET() {
  return Response.json(mockFuturesData)
}
