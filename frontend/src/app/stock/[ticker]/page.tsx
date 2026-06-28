// params is a Promise in Next.js 15+
type Params = Promise<{ ticker: string }>

export default async function StockPage({ params }: { params: Params }) {
  const { ticker } = await params

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">個股分析：{ticker}</h1>
      <p className="mt-2 text-zinc-400 text-sm">Step 2 placeholder</p>
    </div>
  )
}
