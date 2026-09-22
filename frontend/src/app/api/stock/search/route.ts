import { DataServiceError, fetchFromDataService } from "@/lib/data-service-client"
import type { TickerSearchResult } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：中台 /stocks/search（twstock.codes 本地代碼表，依代碼前綴或名稱關鍵字搜尋）
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get("q") ?? ""
  try {
    const data = await fetchFromDataService<TickerSearchResult[]>(`/stocks/search?q=${encodeURIComponent(q)}`)
    return Response.json(data)
  } catch (err) {
    console.error("[stock/search route] error:", err)
    const status = err instanceof DataServiceError ? err.status : 500
    return Response.json({ error: "Failed to search stocks" }, { status })
  }
}
