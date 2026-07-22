import { DataServiceError, fetchFromDataService } from "@/lib/data-service-client"
import { mockMonthlyRevenue } from "@/lib/mock-data"
import type { StockProfile } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料（中台 /stocks/{ticker}/profile）：產業別/上市櫃別來自 twstock，本益比/
// 股價淨值比/殖利率/市值/股本來自 yfinance .info；月營收沒有真實來源，用本地 mock 補上。
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  try {
    const data = await fetchFromDataService<Omit<StockProfile, "monthly_revenue">>(`/stocks/${ticker}/profile`)
    return Response.json({ ...data, monthly_revenue: mockMonthlyRevenue })
  } catch (err) {
    console.error("[stock/profile route] error:", err)
    const status = err instanceof DataServiceError ? err.status : 500
    return Response.json({ error: "Failed to fetch stock profile" }, { status })
  }
}
