import { runPythonModule } from "@/lib/run-python"
import type { FundamentalAnalysis } from "@/lib/types"

export const dynamic = "force-dynamic"

export async function GET(request: Request, { params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params
  if (!/^\d{4}$/.test(ticker)) {
    return Response.json({ error: "股票代碼格式不正確" }, { status: 400 })
  }
  try {
    const data = await runPythonModule<FundamentalAnalysis>("screen_fundamental", [ticker], {
      timeout: 180_000, signal: request.signal,
    })
    if (!data.rules?.length) {
      return Response.json({ error: "暫時無法載入基本面研究資料" }, { status: data.status === "invalid_data" ? 404 : 503 })
    }
    return Response.json(data)
  } catch {
    return Response.json({ error: "暫時無法載入基本面研究資料" }, { status: 503 })
  }
}
