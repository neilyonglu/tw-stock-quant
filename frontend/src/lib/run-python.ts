import { execFile } from "child_process"
import { promisify } from "util"
import path from "path"

const execFileAsync = promisify(execFile)

// 抓資料一律走中台（data-service-client.ts 打 data_service/ 的 HTTP API）。這支 helper
// 現在只剩 get_stock_data.py 在用——那是隊友的後端 merge 回 main 前的技術指標計算佔位層
// （SMA/RSI/MACD，跟中台要 raw candles 後在本地算），等後端 merge 完就會整支刪除，
// 屆時這個 helper 也可以一起移除。詳見 PROJECT.md「架構：中台 / 前端 / 後端」。
// PATH 上的 python3 在 Windows 常解析到 Microsoft Store 的 app-execution-alias stub，
// 不是專案 .venv（沒裝 yfinance/pandas），跑起來沒有 stdout 也沒有錯誤訊息，只會讓呼叫端
// JSON.parse 失敗。改用 uv 直接在專案虛擬環境裡跑腳本，避免依賴系統 PATH 解析到哪個 python。

export async function runPythonScript<T>(scriptName: string, args: string[]): Promise<T> {
  const projectRoot = path.resolve(process.cwd(), "..")
  const script = path.join(projectRoot, "src", "api", scriptName)
  const { stdout } = await execFileAsync("uv", ["run", "python", script, ...args], {
    cwd: projectRoot,
    timeout: 30_000,
  })
  return JSON.parse(stdout) as T
}