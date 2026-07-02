"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { StatCard } from "@/components/stat-card"
import type { StockChipData } from "@/lib/types"
import { formatDate } from "@/lib/utils"

function fmtSigned(n: number) {
  const sign = n >= 0 ? "+" : ""
  return `${sign}${n.toLocaleString()}`
}

export function ChipTab({ ticker }: { ticker: string }) {
  const [data, setData] = useState<StockChipData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setData(null)
    fetch(`/api/stock/${ticker}/chip`)
      .then((res) => res.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [ticker])

  if (loading || !data) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <StatCard
          label="融資餘額"
          value={`${data.margin_balance.toLocaleString()} 張`}
          sub={fmtSigned(data.margin_balance_change)}
          valueClassName={data.margin_balance_change >= 0 ? "text-red-400" : "text-emerald-400"}
          hint="散戶借錢買股，餘額持續攀升代表籌碼浮動、容易追高被套"
        />
        <StatCard
          label="融券餘額"
          value={`${data.short_balance.toLocaleString()} 張`}
          sub={fmtSigned(data.short_balance_change)}
          valueClassName={data.short_balance_change >= 0 ? "text-red-400" : "text-emerald-400"}
          hint="借股票來放空，餘額大增代表有人看空；回補時反而會推升股價"
        />
        <StatCard
          label="千張大戶持股比例"
          value={`${data.big_holder_ratio.toFixed(1)}%`}
          hint="持有超過 1000 張的大戶占比，比例越高代表籌碼越集中在大戶手上"
        />
      </div>

      <div>
        <p className="text-sm text-zinc-400 mb-2">三大法人近 5 日買賣超（張）</p>
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400">日期</TableHead>
              <TableHead className="text-zinc-400 text-right">外資</TableHead>
              <TableHead className="text-zinc-400 text-right">投信</TableHead>
              <TableHead className="text-zinc-400 text-right">自營商</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.institutional.map((row) => (
              <TableRow key={row.date} className="border-zinc-800 hover:bg-zinc-900">
                <TableCell className="text-zinc-200">{formatDate(row.date)}</TableCell>
                <TableCell className={`text-right tabular-nums ${row.foreign >= 0 ? "text-red-400" : "text-emerald-400"}`}>
                  {fmtSigned(row.foreign)}
                </TableCell>
                <TableCell className={`text-right tabular-nums ${row.trust >= 0 ? "text-red-400" : "text-emerald-400"}`}>
                  {fmtSigned(row.trust)}
                </TableCell>
                <TableCell className={`text-right tabular-nums ${row.dealer >= 0 ? "text-red-400" : "text-emerald-400"}`}>
                  {fmtSigned(row.dealer)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <p className="text-xs text-zinc-500 mt-2">外資連續買超通常是最值得參考的籌碼訊號，因為外資資金量體最大</p>
      </div>
    </div>
  )
}
