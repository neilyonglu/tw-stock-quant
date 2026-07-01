import { DataServiceError, fetchFromDataService } from "@/lib/data-service-client"
import type { OrderBookData } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：中台 /stocks/{ticker}/orderbook（twstock.realtime 即時五檔，免金鑰）
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  try {
    const data = await fetchFromDataService<OrderBookData>(`/stocks/${ticker}/orderbook`)
    return Response.json(data)
  } catch (err) {
    console.error("[stock/orderbook route] error:", err)
    const status = err instanceof DataServiceError ? err.status : 500
    return Response.json({ error: "Failed to fetch order book" }, { status })
  }
}
