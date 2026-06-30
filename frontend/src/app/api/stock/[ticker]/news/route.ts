import { NextRequest } from "next/server"
import { mockStockNews } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// mock：個股新聞，Phase 6 規劃的 feedparser 還沒接（見 lib/types.ts NewsItem 說明）
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  const name = request.nextUrl.searchParams.get("name") ?? ticker
  return Response.json({ items: mockStockNews(name) })
}
