import { runPythonScript } from "@/lib/run-python"
import type { OrderBookData } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：twstock.realtime 直接拿 TWSE/TPEx 即時五檔，免金鑰
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  try {
    const data = await runPythonScript<OrderBookData & { error?: string }>("get_orderbook.py", [ticker])
    if ("error" in data) {
      return Response.json({ error: data.error }, { status: 404 })
    }
    return Response.json(data)
  } catch (err) {
    console.error("[stock/orderbook route] error:", err)
    return Response.json({ error: "Failed to fetch order book" }, { status: 500 })
  }
}
