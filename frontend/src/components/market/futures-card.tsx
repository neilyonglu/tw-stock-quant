"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { StatCard } from "@/components/stat-card"
import { MockNotice } from "@/components/mock-badge"
import type { FuturesData } from "@/lib/types"

export function FuturesCard() {
  const [data, setData] = useState<FuturesData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/market/futures")
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) throw new Error(json.error ?? "Unknown error")
        setData(json)
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load data"))
  }, [])

  if (error) {
    return (
      <div className="flex items-center justify-center h-24 text-sm text-muted-foreground">
        暫時無法載入期貨資料（資料服務可能未啟動）
      </div>
    )
  }

  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <MockNotice reason="無免費資料來源，台指期與外資未平倉要另找券商 API" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <StatCard
          label="台指期（近月）"
          value={data.tx_price.toLocaleString()}
          sub={`${data.tx_change >= 0 ? "+" : ""}${data.tx_change}`}
          valueClassName={data.tx_change >= 0 ? "text-red-400" : "text-emerald-400"}
          hint="期貨價格反映市場對未來的預期，常比現貨更早反應消息"
        />
        <StatCard
          label="正逆價差"
          value={`${data.basis >= 0 ? "+" : ""}${data.basis}`}
          valueClassName={data.basis >= 0 ? "text-red-400" : "text-emerald-400"}
          hint="期貨價格 - 現貨價格；正價差代表市場偏多，逆價差代表偏空"
        />
        <StatCard
          label="外資台指期淨未平倉"
          value={`${data.foreign_oi >= 0 ? "+" : ""}${data.foreign_oi.toLocaleString()} 口`}
          valueClassName={data.foreign_oi >= 0 ? "text-red-400" : "text-emerald-400"}
          hint="正數代表外資整體偏多單，是判斷外資對大盤看法的指標"
        />
      </div>
    </div>
  )
}
