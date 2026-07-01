import { DataServiceError, fetchFromDataService } from "@/lib/data-service-client"
import type { MarketIndicesData } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：中台 /market/indices（yfinance ^TWII / ^TWOII / 國際指數，免金鑰）
export async function GET() {
  try {
    const data = await fetchFromDataService<MarketIndicesData>("/market/indices")
    return Response.json(data)
  } catch (err) {
    console.error("[market/indices route] error:", err)
    const status = err instanceof DataServiceError ? err.status : 500
    return Response.json({ error: "Failed to fetch market indices" }, { status })
  }
}
