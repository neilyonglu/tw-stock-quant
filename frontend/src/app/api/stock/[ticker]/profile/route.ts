import { runPythonScript } from "@/lib/run-python"
import type { StockProfile } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：產業別/上市櫃別來自 twstock，本益比/股價淨值比/殖利率/市值/股本來自
// yfinance .info；月營收是 mock（見 get_stock_profile.py 說明）
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  try {
    const data = await runPythonScript<StockProfile>("get_stock_profile.py", [ticker])
    return Response.json(data)
  } catch (err) {
    console.error("[stock/profile route] error:", err)
    return Response.json({ error: "Failed to fetch stock profile" }, { status: 500 })
  }
}
