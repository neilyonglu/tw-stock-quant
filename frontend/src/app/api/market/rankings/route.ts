import { mockMarketRankings } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// mock：類股/成交量/漲跌幅排行，需要全市場掃描，Phase 1 + Phase 6 做完才能換真的
export async function GET() {
  return Response.json(mockMarketRankings)
}
