import { execFile } from "child_process"
import { promisify } from "util"
import path from "path"

const execFileAsync = promisify(execFile)

// 抓資料一律走中台（data-service-client.ts 打 data_service/ 的 HTTP API）。這支 helper
// 現在只剩 get_stock_data.py 在用——那是隊友的後端 merge 回 main 前的技術指標計算佔位層
// （SMA/RSI/MACD，跟中台要 raw candles 後在本地算），等後端 merge 完就會整支刪除，
// 屆時這個 helper 也可以一起移除。詳見 docs/thinking.md 2026-07-01「拆出資料中台」。
export async function runPythonScript<T>(scriptName: string, args: string[]): Promise<T> {
  const script = path.resolve(process.cwd(), "..", "src", "api", scriptName)
  const { stdout } = await execFileAsync("python3", [script, ...args], { timeout: 30_000 })
  return JSON.parse(stdout) as T
}
