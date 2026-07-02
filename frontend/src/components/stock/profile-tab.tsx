"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { StatCard } from "@/components/stat-card"
import type { StockProfile } from "@/lib/types"
import { formatDate } from "@/lib/utils"

export function ProfileTab({ ticker }: { ticker: string }) {
  const [data, setData] = useState<StockProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setData(null)
    fetch(`/api/stock/${ticker}/profile`)
      .then((res) => res.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [ticker])

  if (loading || !data) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(9)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="本益比（PE）"
          value={data.pe_ratio != null ? data.pe_ratio.toFixed(1) : "—"}
          hint="股價 ÷ 每股盈餘，數字越低代表用越便宜的價格買到獲利"
        />
        <StatCard
          label="股價淨值比（PB）"
          value={data.pb_ratio != null ? data.pb_ratio.toFixed(2) : "—"}
          hint="股價 ÷ 每股淨值，PB < 1 代表股價低於公司帳面價值"
        />
        <StatCard
          label="殖利率"
          value={data.dividend_yield != null ? `${data.dividend_yield.toFixed(2)}%` : "—"}
          hint="股息 ÷ 股價，數字越高代表領股息的報酬率越高"
        />
        <StatCard
          label="每股盈餘（EPS）"
          value={data.eps != null ? data.eps.toFixed(2) : "—"}
          hint="近 12 個月公司每股賺多少錢，是本益比的計算基礎"
        />
        <StatCard
          label="52 週高低"
          value={data.week52_high != null ? data.week52_high.toLocaleString() : "—"}
          sub={data.week52_low != null ? `低 ${data.week52_low.toLocaleString()}` : undefined}
          hint="近一年股價的最高、最低點，可以看出目前位階是偏高還偏低"
        />
        <StatCard
          label="市值"
          value={`${data.market_cap.toLocaleString()} 億`}
          hint="公司現在市場上值多少錢，數字越大通常代表越穩定、波動較小"
        />
        <StatCard
          label="股本"
          value={`${data.shares_outstanding.toFixed(2)} 億股`}
          hint="公司發行的股票總數，股本越大、股價要上漲所需資金越多"
        />
        <StatCard
          label="產業別 / 上市櫃"
          value={data.industry}
          sub={data.listed_market}
          hint="同產業的股票表現常常連動，可以拿來跟同業比較"
        />
        <StatCard
          label="分析師目標價"
          value={data.analyst_target != null ? data.analyst_target.toLocaleString() : "—"}
          sub={data.analyst_count != null ? `${data.analyst_count} 位分析師` : undefined}
          hint="華爾街分析師對股價的平均預期，僅供參考、不是保證"
        />
      </div>

      <div>
        <p className="text-sm text-zinc-400 mb-2">近 6 個月營收</p>
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400">月份</TableHead>
              <TableHead className="text-zinc-400 text-right">營收（億元）</TableHead>
              <TableHead className="text-zinc-400 text-right">年增率 YoY</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.monthly_revenue.map((r) => (
              <TableRow key={r.month} className="border-zinc-800 hover:bg-zinc-900">
                <TableCell className="text-zinc-200">{formatDate(r.month)}</TableCell>
                <TableCell className="text-right tabular-nums text-zinc-200">{r.revenue.toLocaleString()}</TableCell>
                <TableCell className={`text-right tabular-nums ${r.yoy >= 0 ? "text-red-400" : "text-emerald-400"}`}>
                  {r.yoy >= 0 ? "+" : ""}{r.yoy.toFixed(1)}%
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <p className="text-xs text-zinc-500 mt-2">月營收 YoY 是最即時的基本面訊號，每月 10 日前公布；YoY &gt; 10% 代表成長動能強</p>
      </div>
    </div>
  )
}
