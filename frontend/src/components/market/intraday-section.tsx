"use client"

import { useEffect, useState } from "react"
import { formatTimeShort } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { IntradayChart } from "@/components/charts/intraday-chart"
import type { IntradaySeries } from "@/lib/types"

export function MarketIntradaySection({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<IntradaySeries | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    fetch("/api/market/intraday", { signal: ctrl.signal })
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok || json.error) throw new Error(json.error ?? "Unknown error")
        setError(null)
        setData(json)
      })
      .catch((e: unknown) => {
        if (e instanceof Error && e.name === "AbortError") return
        setError(e instanceof Error ? e.message : "Failed to load data")
      })
    return () => ctrl.abort()
  }, [refreshKey])

  const lastPoint = data?.points.at(-1)
  return (
    <div>
      <p className="text-sm text-zinc-400 mb-2">加權指數分時走勢</p>
      {error && <div className="h-50 flex items-center justify-center text-muted-foreground text-sm">暫時無法載入分時走勢（非交易時段可能沒有今日資料）</div>}
      {!error && !data && <Skeleton className="h-100 w-full bg-zinc-900" />}
      {!error && data && <>
        <p className="text-xs text-muted-foreground mb-2">資料時間 {lastPoint ? formatTimeShort(new Date(lastPoint.time * 1000).toISOString()) : "—"}</p>
        <IntradayChart data={data} />
      </>}
    </div>
  )
}
