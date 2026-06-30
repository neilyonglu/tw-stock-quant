"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { NewsList } from "@/components/news-list"
import type { NewsItem } from "@/lib/types"

export function MarketNewsSection() {
  const [items, setItems] = useState<NewsItem[] | null>(null)

  useEffect(() => {
    fetch("/api/market/news").then((res) => res.json()).then((json) => setItems(json.items))
  }, [])

  return (
    <div>
      <p className="text-sm text-zinc-400 mb-2">新聞快訊（mock）</p>
      <div className="bg-zinc-900 border border-zinc-800 rounded-md px-4">
        {!items ? (
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
