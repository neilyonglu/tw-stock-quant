"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { NewsList } from "@/components/news-list"
import { MockNotice } from "@/components/mock-badge"
import type { NewsItem } from "@/lib/types"

export function NewsTab({ ticker, name }: { ticker: string; name?: string }) {
  const [items, setItems] = useState<NewsItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    setItems(null)
    setError(null)
    const qs = name ? `?name=${encodeURIComponent(name)}` : ""
    fetch(`/api/stock/${ticker}/news${qs}`, { signal: ctrl.signal })
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) throw new Error(json.error ?? "Unknown error")
        setItems(json.items)
      })
      .catch((e: unknown) => {
        if (e instanceof Error && e.name === "AbortError") return
        setError(e instanceof Error ? e.message : "Failed to load data")
      })
    return () => ctrl.abort()
  }, [ticker, name])

  if (error) {
    return (
      <div className="space-y-2">
        <MockNotice reason="個股新聞牆要另找來源（Phase 6 規劃 TWSE 重大訊息 RSS）" />
        <div className="flex items-center justify-center h-14 text-sm text-muted-foreground">
          暫時無法載入新聞（資料服務可能未啟動）
        </div>
      </div>
    )
  }

  if (!items) {
    return (
      <div className="space-y-2">
        <MockNotice reason="個股新聞牆要另找來源（Phase 6 規劃 TWSE 重大訊息 RSS）" />
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-14 bg-zinc-900" />)}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <MockNotice reason="個股新聞牆要另找來源（Phase 6 規劃 TWSE 重大訊息 RSS）" />
      <NewsList items={items} />
    </div>
  )
}
