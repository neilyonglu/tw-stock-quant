import { runPythonScript } from "@/lib/run-python"
import type { IntradaySeries } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：yfinance 今日 1 分鐘 K，跟大盤分時走勢共用 get_intraday.py
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  try {
    const data = await runPythonScript<IntradaySeries & { error?: string }>("get_intraday.py", [`${ticker}.TW`])
    if ("error" in data) {
      return Response.json({ error: data.error }, { status: 404 })
    }
    return Response.json(data)
  } catch (err) {
    console.error("[stock/intraday route] error:", err)
    return Response.json({ error: "Failed to fetch stock intraday data" }, { status: 500 })
  }
}
