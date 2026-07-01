"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { ArrowDown, ArrowUp, ArrowUpDown, Download, RotateCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Pie, PieChart, Cell } from "recharts"
import { cn } from "@/lib/utils"
import type { ScreeningData, ScreeningResult } from "@/lib/types"

// 台股慣例：紅漲綠跌，多頭（看漲）用紅、空頭（看跌）用綠
const ENV_TEXT: Record<ScreeningData["market_environment"], string> = {
  多頭: "text-red-400",
  盤整: "text-amber-400",
  空頭: "text-emerald-400",
}

const PIE_COLORS = ["#3B82F6", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899", "#71717A"]

type SortKey = "rank" | "score" | "allocation_pct"

function scoreBadgeVariant(score: number): "default" | "secondary" | "outline" {
  if (score >= 80) return "default"
  if (score >= 60) return "secondary"
  return "outline"
}

function toCsv(results: ScreeningResult[]): string {
  const header = ["排名", "代碼", "名稱", "評分", "進場低", "進場高", "停損", "停損%", "配置%"]
  const rows = results.map((r) => [
    r.rank,
    r.ticker,
    r.name,
    r.score,
    r.entry_low,
    r.entry_high,
    r.stop_loss,
    r.stop_loss_pct,
    r.allocation_pct,
  ])
  return [header, ...rows].map((row) => row.join(",")).join("\n")
}

function downloadCsv(results: ScreeningResult[]) {
  const blob = new Blob(["﻿" + toCsv(results)], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `screening-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function SortButton({
  label,
  sortKey,
  activeKey,
  dir,
  onClick,
}: {
  label: string
  sortKey: SortKey
  activeKey: SortKey
  dir: "asc" | "desc"
  onClick: () => void
}) {
  const Icon = activeKey !== sortKey ? ArrowUpDown : dir === "asc" ? ArrowUp : ArrowDown
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1 hover:text-white transition-colors"
    >
      {label}
      <Icon size={12} className={activeKey === sortKey ? "text-white" : "text-zinc-600"} />
    </button>
  )
}

export function ScreeningView() {
  const [data, setData] = useState<ScreeningData | null>(null)
  const [loading, setLoading] = useState(true)
  const [sortKey, setSortKey] = useState<SortKey>("rank")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc")

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/screening")
      setData(await res.json())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  const sortedResults = useMemo(() => {
    if (!data) return []
    const copy = [...data.results]
    copy.sort((a, b) => {
      const diff = a[sortKey] - b[sortKey]
      return sortDir === "asc" ? diff : -diff
    })
    return copy
  }, [data, sortKey, sortDir])

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* 標題列 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">每週選股結果</h1>
          {data && (
            <p className="text-xs text-zinc-500 mt-1 flex items-center gap-2">
              資料時間：{new Date(data.updated_at).toLocaleString("zh-TW")}
              <span className="text-zinc-700">|</span>
              市場環境：<span className={ENV_TEXT[data.market_environment]}>{data.market_environment}</span>
            </p>
          )}
        </div>
        <Button variant="outline" size="sm" className="border-zinc-700" onClick={fetchData} disabled={loading}>
          <RotateCw size={14} className={loading ? "animate-spin" : ""} />
          重新整理
        </Button>
      </div>

      {loading || !data ? (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          <Skeleton className="h-96 bg-zinc-900" />
          <Skeleton className="h-96 bg-zinc-900" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          {/* 選股表格 */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableHead className="text-zinc-400">
                    <SortButton label="#" sortKey="rank" activeKey={sortKey} dir={sortDir} onClick={() => toggleSort("rank")} />
                  </TableHead>
                  <TableHead className="text-zinc-400">股票</TableHead>
                  <TableHead className="text-zinc-400">
                    <SortButton label="評分" sortKey="score" activeKey={sortKey} dir={sortDir} onClick={() => toggleSort("score")} />
                  </TableHead>
                  <TableHead className="text-zinc-400 min-w-48">推薦理由</TableHead>
                  <TableHead className="text-zinc-400">進場區間</TableHead>
                  <TableHead className="text-zinc-400">停損</TableHead>
                  <TableHead className="text-zinc-400">
                    <SortButton label="配置 %" sortKey="allocation_pct" activeKey={sortKey} dir={sortDir} onClick={() => toggleSort("allocation_pct")} />
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedResults.map((r) => (
                  <TableRow key={r.ticker} className="border-zinc-800">
                    <TableCell className="tabular-nums text-zinc-400">{r.rank}</TableCell>
                    <TableCell>
                      <Link href={`/stock/${r.ticker}`} className="hover:text-red-400 transition-colors">
                        <span className="font-medium text-white">{r.name}</span>
                        <span className="text-zinc-500 ml-1.5 tabular-nums">{r.ticker}</span>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={scoreBadgeVariant(r.score)} className="tabular-nums">
                        {r.score}
                      </Badge>
                    </TableCell>
                    <TableCell className="whitespace-normal">
                      <ul className="text-xs text-zinc-500 space-y-0.5 leading-snug">
                        <li><span className="text-zinc-600">法人｜</span>{r.reasons.institutional}</li>
                        <li><span className="text-zinc-600">技術｜</span>{r.reasons.technical}</li>
                        <li><span className="text-zinc-600">基本面｜</span>{r.reasons.fundamental}</li>
                      </ul>
                    </TableCell>
                    <TableCell className="tabular-nums text-zinc-300">
                      {r.entry_low}–{r.entry_high}
                    </TableCell>
                    <TableCell className="tabular-nums">
                      <span className="text-emerald-400">{r.stop_loss}</span>
                      <span className="text-zinc-500 ml-1">({r.stop_loss_pct}%)</span>
                    </TableCell>
                    <TableCell className="min-w-24">
                      <div className="flex items-center gap-2">
                        <span className="tabular-nums text-zinc-300 w-9">{r.allocation_pct}%</span>
                        <Progress value={r.allocation_pct} className="w-16" />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* 投組配置圓餅圖 */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
            <p className="text-sm text-zinc-400 mb-2">建議投組配置</p>
            <ChartContainer
              config={Object.fromEntries(data.allocation.map((a) => [a.name, { label: a.name }]))}
              className="mx-auto aspect-square max-h-64"
            >
              <PieChart>
                <ChartTooltip content={<ChartTooltipContent nameKey="name" hideLabel />} />
                <Pie
                  data={data.allocation}
                  dataKey="pct"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={90}
                  strokeWidth={2}
                  isAnimationActive={false}
                >
                  {data.allocation.map((entry, i) => (
                    <Cell key={entry.name} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ChartContainer>
            <div className="mt-3 space-y-1.5">
              {data.allocation.map((a, i) => (
                <div key={a.name} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-zinc-400">
                    <span
                      className="inline-block w-2 h-2 rounded-full"
                      style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                    />
                    {a.name}
                  </span>
                  <span className="tabular-nums text-zinc-300">{a.pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <Button
        variant="outline"
        size="sm"
        className="border-zinc-700"
        disabled={!data}
        onClick={() => data && downloadCsv(data.results)}
      >
        <Download size={14} />
        下載 CSV
      </Button>

      <p className={cn("text-xs text-zinc-500")}>
        評分、進場區間、停損與投組配置是模擬資料，實際策略邏輯還在開發中，不構成投資建議。
      </p>
    </div>
  )
}
