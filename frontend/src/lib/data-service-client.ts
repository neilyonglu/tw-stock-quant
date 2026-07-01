// 中台（data_service/，FastAPI）是唯一負責抓取＋快取外部資料的服務，前端 Route Handler
// 一律透過這支 helper 打中台的 HTTP API，不直接呼叫 yfinance/twstock。
// 詳見 docs/thinking.md 2026-07-01「拆出資料中台」。
const DATA_SERVICE_URL = process.env.DATA_SERVICE_URL ?? "http://localhost:8001"

export class DataServiceError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export async function fetchFromDataService<T>(path: string): Promise<T> {
  const res = await fetch(`${DATA_SERVICE_URL}${path}`, { cache: "no-store" })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new DataServiceError(res.status, detail.detail ?? `data-service ${path} failed`)
  }
  return res.json() as Promise<T>
}
