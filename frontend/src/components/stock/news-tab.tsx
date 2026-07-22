"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { NewsList } from "@/components/news-list"
import type { NewsItem } from "@/lib/types"

export function NewsTab({ ticker, name }: { ticker: string; name?: string }) {
  const [items, setItems] = useState<NewsItem[] | null>(null)

  useEffect(() => {
    setItems(null)
    const qs = name ? `?name=${encodeURIComponent(name)}` : ""
    fetch(`/api/stock/${ticker}/news${qs}`)
      .then((res) => res.json())
      .then((json) => setItems(json.items))
  }, [ticker, name])

  if (!items) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-14 bg-zinc-900" />)}
      </div>
    )
  }

  return <NewsList items={items} />
}
