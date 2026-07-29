"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Skeleton } from "@/components/ui/skeleton"
import { TickerSearch } from "@/components/ticker-search"
import type { MarketRankings, RankedItem } from "@/lib/types"

function RankRow({ item }: { item: RankedItem }) {
  const isUp = item.value >= 0
  return (
    <Link
      href={`/stock/${item.ticker}`}
      className="flex items-center justify-between gap-3 py-2.5 px-1 min-h-11 rounded-md hover:bg-zinc-900 transition-colors"
    >
      <span className="text-sm text-zinc-200 truncate">
        <span className="text-muted-foreground mr-1.5">{item.ticker}</span>
        {item.name}
      </span>
      <span className={`text-sm font-medium tabular-nums shrink-0 ${isUp ? "text-red-400" : "text-emerald-400"}`}>
        {isUp ? "+" : ""}
        {item.value.toLocaleString()}
        {item.unit}
      </span>
    </Link>
  )
}

export function StockHomeView() {
  const router = useRouter()
  const [rankings, setRankings] = useState<MarketRankings | null>(null)

  useEffect(() => {
    fetch("/api/market/rankings")
      .then((res) => res.json())
      .then(setRankings)
  }, [])

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">個股分析</h1>
        <p className="text-xs text-muted-foreground mt-1">輸入代碼或名稱查個股，或從下面排行榜點進去</p>
      </div>

      {/* 搜尋 */}
      <div className="max-w-sm">
        <TickerSearch onSelect={(t) => router.push(`/stock/${t}`)} />
      </div>

      {/* 排行榜（示範資料） */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <p className="text-sm font-medium text-zinc-200">今日漲跌幅前五名</p>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30">
            示範資料，非真實排行
          </span>
        </div>

        {!rankings ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[0, 1].map((i) => (
              <div key={i} className="space-y-2">
                {[...Array(5)].map((_, j) => (
                  <Skeleton key={j} className="h-9 w-full bg-zinc-900" />
                ))}
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">漲幅排行</p>
              <div className="border-t border-zinc-800">
                {rankings.gainers.slice(0, 5).map((item) => (
                  <RankRow key={item.ticker} item={item} />
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">跌幅排行</p>
              <div className="border-t border-zinc-800">
                {rankings.losers.slice(0, 5).map((item) => (
                  <RankRow key={item.ticker} item={item} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
