"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { Star, X } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useWatchlist, removeFromWatchlist } from "@/lib/watchlist"
import { formatTimeShort } from "@/lib/utils"
import type { StockData } from "@/lib/types"

function fmtChange(change: number, pct: number) {
  const sign = change >= 0 ? "+" : ""
  return `${sign}${change.toFixed(2)} (${sign}${pct.toFixed(2)}%)`
}

export function WatchlistView() {
  const tickers = useWatchlist()
  const [quotes, setQuotes] = useState<Record<string, StockData | null>>({})
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchQuotes = useCallback(async (list: string[], silent = false) => {
    if (list.length === 0) {
      setQuotes({})
      setLoading(false)
      return
    }
    if (!silent) setLoading(true)
    try {
      const results = await Promise.all(
        list.map(async (ticker) => {
          try {
            const res = await fetch(`/api/stock/${ticker}?period=1mo&interval=1d`)
            if (!res.ok) return [ticker, null] as const
            return [ticker, (await res.json()) as StockData] as const
          } catch {
            return [ticker, null] as const
          }
        })
      )
      setQuotes(Object.fromEntries(results))
      setLastUpdated(new Date())
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchQuotes(tickers)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tickers.join(","), fetchQuotes])

  // 定期背景刷新（報價中台快取 30 秒 TTL），分頁在背景時暫停，切回前景立刻補刷一次
  useEffect(() => {
    function tick() {
      if (document.hidden) return
      fetchQuotes(tickers, true)
    }
    const timer = setInterval(tick, 30_000)
    function onVisible() {
      if (!document.hidden) tick()
    }
    document.addEventListener("visibilitychange", onVisible)
    return () => {
      clearInterval(timer)
      document.removeEventListener("visibilitychange", onVisible)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tickers.join(","), fetchQuotes])

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">自選股</h1>
          <p className="text-xs text-muted-foreground mt-1">
            存在這台電腦的瀏覽器，換裝置或清瀏覽器資料會消失。
            {lastUpdated && <> 更新於 {formatTimeShort(lastUpdated.toISOString())}</>}
          </p>
        </div>
      </div>

      {tickers.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center border border-dashed border-zinc-800 rounded-lg">
          <Star size={28} className="text-zinc-600" />
          <p className="text-sm text-muted-foreground">
            還沒有自選股。到{" "}
            <Link href="/stock/2330" className="text-sidebar-primary hover:underline">
              個股頁面
            </Link>{" "}
            點標題旁的星星加入。
          </p>
        </div>
      ) : (
        <div className="border border-zinc-800 rounded-lg overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead>代碼</TableHead>
                <TableHead>名稱</TableHead>
                <TableHead className="text-right">股價</TableHead>
                <TableHead className="text-right">漲跌</TableHead>
                <TableHead className="w-11" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {tickers.map((ticker) => {
                const quote = quotes[ticker]
                const latest = quote?.latest
                const isUp = (latest?.change ?? 0) >= 0
                return (
                  <TableRow key={ticker} className="border-zinc-800">
                    <TableCell className="font-medium">
                      <Link href={`/stock/${ticker}`} className="hover:underline">
                        {ticker}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {loading && !quote ? <Skeleton className="h-4 w-16 bg-zinc-800" /> : quote?.name ?? "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {loading && !quote ? (
                        <Skeleton className="h-4 w-12 bg-zinc-800 ml-auto" />
                      ) : latest ? (
                        latest.price.toLocaleString()
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell
                      className={`text-right tabular-nums ${
                        latest ? (isUp ? "text-red-400" : "text-emerald-400") : ""
                      }`}
                    >
                      {latest ? fmtChange(latest.change, latest.change_pct) : "—"}
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => removeFromWatchlist(ticker)}
                        aria-label={`移除 ${ticker}`}
                        className="flex items-center justify-center h-11 w-11 -my-3.5 -mx-2.5 rounded-md text-zinc-500 hover:text-red-400 transition-colors"
                      >
                        <X size={14} />
                      </button>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
