import { runPythonScript } from "@/lib/run-python"
import type { IntradaySeries } from "@/lib/types"

export const dynamic = "force-dynamic"

// 真實資料：yfinance ^TWII 1 分鐘 K，跟個股分時走勢共用 get_intraday.py
export async function GET() {
  try {
    const data = await runPythonScript<IntradaySeries & { error?: string }>("get_intraday.py", ["^TWII"])
    if ("error" in data) {
      return Response.json({ error: data.error }, { status: 404 })
    }
    return Response.json(data)
  } catch (err) {
    console.error("[market/intraday route] error:", err)
    return Response.json({ error: "Failed to fetch market intraday data" }, { status: 500 })
  }
}
