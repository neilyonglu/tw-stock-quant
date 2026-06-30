"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table"
import type { MarketRankings, RankedItem } from "@/lib/types"

function RankTable({ items, positiveIsUp }: { items: RankedItem[]; positiveIsUp: boolean }) {
  return (
    <Table>
      <TableBody>
        {items.map((item, i) => (
          <TableRow key={item.ticker ?? item.name} className="border-zinc-800 hover:bg-zinc-900">
            <TableCell className="text-zinc-500 w-8">{i + 1}</TableCell>
            <TableCell className="text-zinc-200">
              {item.ticker && <span className="text-zinc-500 mr-1.5">{item.ticker}</span>}
              {item.name}
            </TableCell>
            <TableCell
              className={`text-right tabular-nums ${
                !positiveIsUp ? "text-zinc-200" : item.value >= 0 ? "text-red-400" : "text-emerald-400"
              }`}
            >
              {positiveIsUp && item.value >= 0 ? "+" : ""}
              {item.value.toLocaleString()}
              {item.unit}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function RankingsSection() {
  const [data, setData] = useState<MarketRankings | null>(null)

  useEffect(() => {
    fetch("/api/market/rankings").then((res) => res.json()).then(setData)
  }, [])

  if (!data) {
    return <Skeleton className="h-64 w-full bg-zinc-900" />
  }

  return (
    <div>
      <p className="text-sm text-zinc-400 mb-2">排行榜（mock）</p>
      <Tabs defaultValue="sector">
        <TabsList className="mb-2 bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="sector">類股漲跌幅</TabsTrigger>
          <TabsTrigger value="volume">成交值</TabsTrigger>
          <TabsTrigger value="gainers">漲幅排行</TabsTrigger>
          <TabsTrigger value="losers">跌幅排行</TabsTrigger>
        </TabsList>
        <TabsContent value="sector">
          <RankTable items={data.sector_performance} positiveIsUp />
        </TabsContent>
        <TabsContent value="volume">
          <RankTable items={data.volume_leaders} positiveIsUp={false} />
        </TabsContent>
        <TabsContent value="gainers">
          <RankTable items={data.gainers} positiveIsUp />
        </TabsContent>
        <TabsContent value="losers">
          <RankTable items={data.losers} positiveIsUp />
        </TabsContent>
      </Tabs>
    </div>
  )
}
