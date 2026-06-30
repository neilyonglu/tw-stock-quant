"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import type { OrderBookData } from "@/lib/types"

export function OrderBook({ ticker }: { ticker: string }) {
  const [data, setData] = useState<OrderBookData | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    setData(null)
    setError(false)
    fetch(`/api/stock/${ticker}/orderbook`)
      .then((res) => res.json())
      .then((json) => {
        if (json.error) setError(true)
        else setData(json)
      })
  }, [ticker])

  if (error) {
    return <p className="text-xs text-zinc-500">查無即時報價</p>
  }
  if (!data) {
    return <Skeleton className="h-48 w-full bg-zinc-800" />
  }
  if (data.asks.length === 0 && data.bids.length === 0) {
    return <p className="text-xs text-zinc-500">非交易時段，目前沒有掛單</p>
  }

  const maxVol = Math.max(1, ...data.asks.map((l) => l.volume), ...data.bids.map((l) => l.volume))

  return (
    <div className="text-xs space-y-0.5">
      {[...data.asks].reverse().map((lvl, i) => (
        <Row key={`ask-${i}`} price={lvl.price} volume={lvl.volume} maxVol={maxVol} side="ask" />
      ))}
      <div className="border-t border-zinc-800 my-1" />
      {data.bids.map((lvl, i) => (
        <Row key={`bid-${i}`} price={lvl.price} volume={lvl.volume} maxVol={maxVol} side="bid" />
      ))}
    </div>
  )
}

// 台股慣例紅漲綠跌：委買（買方掛單，撐住股價）用紅、委賣（賣方掛單，壓低股價）用綠
function Row({ price, volume, maxVol, side }: { price: number; volume: number; maxVol: number; side: "ask" | "bid" }) {
  const pct = Math.round((volume / maxVol) * 100)
  const color = side === "bid" ? "text-red-400" : "text-emerald-400"
  const barColor = side === "bid" ? "bg-red-400/15" : "bg-emerald-400/15"
  return (
    <div className="relative flex items-center justify-between px-1.5 py-0.5 rounded-sm overflow-hidden">
      <div className={`absolute inset-y-0 ${side === "bid" ? "right-0" : "left-0"} ${barColor}`} style={{ width: `${pct}%` }} />
      <span className={`relative tabular-nums ${color}`}>{price.toFixed(2)}</span>
      <span className="relative tabular-nums text-zinc-400">{volume}</span>
    </div>
  )
}
