import { NextRequest } from "next/server"
import { mockOrderBook } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// mock：五檔報價，yfinance 沒有委買委賣盤口資料（見 lib/types.ts OrderBookData 說明）。
// price 由前端帶現價過來，沒帶就用預設值，純粹讓假資料的價位看起來合理。
export async function GET(request: NextRequest) {
  const price = Number(request.nextUrl.searchParams.get("price")) || 100
  return Response.json(mockOrderBook(price))
}
