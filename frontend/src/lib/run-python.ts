import { execFile } from "child_process"
import { promisify } from "util"
import path from "path"

const execFileAsync = promisify(execFile)

// 抓資料一律走中台（data-service-client.ts 打 data_service/ 的 HTTP API）。這支 helper
// 只給計算層用：src/api/get_stock_data.py 跟中台要 raw candles，再用 src/indicators 算指標。
// 以模組方式執行（python -m src.api.xxx、cwd=專案根目錄），腳本才能 import src.indicators。
// PATH 上的 python3 在 Windows 常解析到 Microsoft Store 的 app-execution-alias stub，
// 不是專案 .venv（沒裝 yfinance/pandas），跑起來沒有 stdout 也沒有錯誤訊息，只會讓呼叫端
// JSON.parse 失敗。改用 uv 直接在專案虛擬環境裡跑，避免依賴系統 PATH 解析到哪個 python。

export async function runPythonModule<T>(moduleName: string, args: string[]): Promise<T> {
  const projectRoot = path.resolve(process.cwd(), "..")
  const { stdout } = await execFileAsync("uv", ["run", "python", "-m", `src.api.${moduleName}`, ...args], {
    cwd: projectRoot,
    timeout: 30_000,
  })
  return JSON.parse(stdout) as T
}
