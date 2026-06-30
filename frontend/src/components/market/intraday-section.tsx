"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { IntradayChart } from "@/components/charts/intraday-chart"
import type { IntradaySeries } from "@/lib/types"

export function MarketIntradaySection() {
  const [data, setData] = useState<IntradaySeries | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/market/intraday")
      .then((res) => res.json())
      .then((json) => {
        if (json.error) setError(json.error)
        else setData(json)
      })
  }, [])

  return (
    <div>
      <p className="text-sm text-zinc-400 mb-2">加權指數分時走勢</p>
      {error && <div className="h-50 flex items-center justify-center text-zinc-500 text-sm">{error}（非交易時段可能沒有今日資料）</div>}
      {!error && !data && <Skeleton className="h-100 w-full bg-zinc-900" />}
      {data && <IntradayChart data={data} />}
    </div>
  )
}
