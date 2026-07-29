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
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok || json.error) throw new Error(json.error ?? "Unknown error")
        setData(json)
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load data"))
  }, [])

  return (
    <div>
      <p className="text-sm text-zinc-400 mb-2">加權指數分時走勢</p>
      {error && <div className="h-50 flex items-center justify-center text-muted-foreground text-sm">暫時無法載入分時走勢（非交易時段可能沒有今日資料）</div>}
      {!error && !data && <Skeleton className="h-100 w-full bg-zinc-900" />}
      {data && <IntradayChart data={data} />}
    </div>
  )
}
