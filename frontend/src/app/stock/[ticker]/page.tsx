import { StockAnalysisView } from "@/components/stock-analysis-view"

// params is a Promise in Next.js 15+
type Params = Promise<{ ticker: string }>

export default async function StockPage({ params }: { params: Params }) {
  const { ticker } = await params
  return <StockAnalysisView initialTicker={ticker} />
}
