import { mockMarketNews } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// mock：全市場新聞快訊。Phase 6 規劃的 feedparser 只收持倉股的 TWSE 重大訊息，
// 全市場新聞牆要另外找來源，先 mock（見 lib/types.ts NewsItem 說明）
export async function GET() {
  return Response.json({ items: mockMarketNews })
}
