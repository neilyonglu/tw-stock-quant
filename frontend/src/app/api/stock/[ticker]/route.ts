import { execFile } from "child_process"
import { promisify } from "util"
import path from "path"
import { NextRequest } from "next/server"

export const dynamic = "force-dynamic"

const execFileAsync = promisify(execFile)
const SCRIPT = path.resolve(process.cwd(), "..", "src", "api", "get_stock_data.py")

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  const period = request.nextUrl.searchParams.get("period") ?? "6mo"

  try {
    const { stdout } = await execFileAsync("python3", [SCRIPT, ticker, period], {
      timeout: 30_000,
    })
    const data = JSON.parse(stdout)
    if (data.error) {
      return Response.json({ error: data.error }, { status: 404 })
    }
    return Response.json(data)
  } catch (err) {
    console.error("[stock route] error:", err)
    return Response.json({ error: "Failed to fetch stock data" }, { status: 500 })
  }
}
