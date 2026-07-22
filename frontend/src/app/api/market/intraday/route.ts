import { DataServiceError, fetchFromDataService } from "@/lib/data-service-client"
import type { IntradaySeries } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：中台 /market/intraday（yfinance ^TWII 1 分鐘 K）
export async function GET() {
  try {
    const data = await fetchFromDataService<IntradaySeries>("/market/intraday")
    return Response.json(data)
  } catch (err) {
    console.error("[market/intraday route] error:", err)
    const status = err instanceof DataServiceError ? err.status : 500
    return Response.json({ error: "Failed to fetch market intraday data" }, { status })
  }
}
