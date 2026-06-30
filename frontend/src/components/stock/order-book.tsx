"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import type { OrderBookData } from "@/lib/types"

export function OrderBook({ ticker, price }: { ticker: string; price: number }) {
  const [data, setData] = useState<OrderBookData | null>(null)

  useEffect(() => {
    if (!price) return
    setData(null)
    fetch(`/api/stock/${ticker}/orderbook?price=${price}`)
      .then((res) => res.json())
      .then(setData)
  }, [ticker, price])

  if (!data) {
    return <Skeleton className="h-48 w-full bg-zinc-800" />
  }

  const maxVol = Math.max(...data.asks.map((l) => l.volume), ...data.bids.map((l) => l.volume))

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
