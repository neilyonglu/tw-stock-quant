import { mockStockChip } from "@/lib/mock-data"

export const dynamic = "force-dynamic"

// mock：個股層級籌碼面，Phase 5 FinMind 做完才能換真的（見 lib/types.ts StockChipData 說明）
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  return Response.json(mockStockChip(ticker))
}
