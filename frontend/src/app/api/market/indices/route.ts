import { runPythonScript } from "@/lib/run-python"
import type { MarketIndicesData } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：yfinance ^TWII / ^TWOII / 國際指數，免金鑰
export async function GET() {
  try {
    const data = await runPythonScript<MarketIndicesData>("get_market_indices.py", [])
    return Response.json(data)
  } catch (err) {
    console.error("[market/indices route] error:", err)
    return Response.json({ error: "Failed to fetch market indices" }, { status: 500 })
  }
}
