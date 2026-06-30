import { execFile } from "child_process"
import { promisify } from "util"
import path from "path"

const execFileAsync = promisify(execFile)

// 建皮期間所有「真實」資料都是 Next.js Route Handler 直接 spawn python3 跑 src/api/*.py，
// 省去 FastAPI server。Phase 9 換成真正後端時，只改呼叫這支 helper 的 route.ts 內部，
// 前端元件不用動（詳見 docs/thinking.md 十四）。
export async function runPythonScript<T>(scriptName: string, args: string[]): Promise<T> {
  const script = path.resolve(process.cwd(), "..", "src", "api", scriptName)
  const { stdout } = await execFileAsync("python3", [script, ...args], { timeout: 30_000 })
  return JSON.parse(stdout) as T
}
