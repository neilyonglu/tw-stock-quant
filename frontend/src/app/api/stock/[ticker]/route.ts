import { NextRequest } from "next/server"
import { runPythonScript } from "@/lib/run-python"
import type { StockData } from "@/lib/types"

export const dynamic = "force-dynamic"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  const period = request.nextUrl.searchParams.get("period") ?? "6mo"
  const interval = request.nextUrl.searchParams.get("interval") ?? "1d"

  try {
    const data = await runPythonScript<StockData & { error?: string }>("get_stock_data.py", [ticker, period, interval])
    if (data.error) {
      return Response.json({ error: data.error }, { status: 404 })
    }
    return Response.json(data)
  } catch (err) {
    console.error("[stock route] error:", err)
    return Response.json({ error: "Failed to fetch stock data" }, { status: 500 })
  }
}
