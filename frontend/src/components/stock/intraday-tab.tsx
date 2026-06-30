"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { IntradayChart } from "@/components/charts/intraday-chart"
import type { IntradaySeries } from "@/lib/types"

export function IntradayTab({ ticker }: { ticker: string }) {
  const [data, setData] = useState<IntradaySeries | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setData(null)
    setError(null)
    fetch(`/api/stock/${ticker}/intraday`)
      .then((res) => res.json())
      .then((json) => {
        if (json.error) setError(json.error)
        else setData(json)
      })
  }, [ticker])

  if (error) {
    return <div className="h-100 flex items-center justify-center text-zinc-500">{error}（非交易時段可能沒有今日分時資料）</div>
  }
  if (!data) {
    return <Skeleton className="h-100 w-full bg-zinc-900" />
  }

  return (
    <div className="space-y-1.5">
      <IntradayChart data={data} />
      <p className="text-xs text-zinc-500">橘線是累計成交均價；灰色虛線是平盤（昨日收盤價）參考線</p>
    </div>
  )
}
