"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { NewsList } from "@/components/news-list"
import { MockBadge } from "@/components/mock-badge"
import type { NewsItem } from "@/lib/types"

export function MarketNewsSection() {
  const [items, setItems] = useState<NewsItem[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch("/api/market/news")
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) throw new Error()
        setItems(json.items)
      })
      .catch(() => setError(true))
  }, [])

  return (
    <div>
      <p className="text-sm text-zinc-400 mb-2 flex items-center gap-1.5">
        新聞快訊
        <MockBadge reason="全市場新聞牆要另找來源（Phase 6 規劃 TWSE 重大訊息 RSS）" />
      </p>
      <div className="bg-zinc-900 border border-zinc-800 rounded-md px-4">
        {error ? (
          <div className="py-6 text-center text-sm text-muted-foreground">暫時無法載入新聞（資料服務可能未啟動）</div>
        ) : !items ? (
          <div className="py-2 space-y-2">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-14 bg-zinc-800" />)}
          </div>
        ) : (
          <NewsList items={items} />
        )}
      </div>
    </div>
  )
}
