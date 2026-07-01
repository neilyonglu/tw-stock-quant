import { DataServiceError, fetchFromDataService } from "@/lib/data-service-client"
import type { IntradaySeries } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：中台 /stocks/{ticker}/intraday（yfinance 今日 1 分鐘 K）
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  try {
    const data = await fetchFromDataService<IntradaySeries>(`/stocks/${ticker}/intraday`)
    return Response.json(data)
  } catch (err) {
    console.error("[stock/intraday route] error:", err)
    const status = err instanceof DataServiceError ? err.status : 500
    return Response.json({ error: "Failed to fetch stock intraday data" }, { status })
  }
}
