"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { Star, X } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useWatchlist, removeFromWatchlist } from "@/lib/watchlist"
import { formatTimeShort } from "@/lib/utils"
import type { StockData, IntradaySeries } from "@/lib/types"

interface WatchRow {
  stock: StockData | null
  intraday: IntradaySeries | null
}

function fmtChange(change: number, pct: number) {
  const sign = change >= 0 ? "+" : ""
  return `${sign}${change.toFixed(2)} (${sign}${pct.toFixed(2)}%)`
}

// 迷你走勢圖：虛線＝平盤參考（昨收），實線顏色跟隨紅漲綠跌
function Sparkline({ points, refValue }: { points: number[]; refValue: number }) {
  const width = 88
  const height = 32
  if (points.length < 2) {
    return <div style={{ width, height }} className="shrink-0" />
  }
  const all = [...points, refValue]
  const min = Math.min(...all)
  const max = Math.max(...all)
  const range = max - min || 1
  const stepX = width / (points.length - 1)
  const y = (v: number) => height - ((v - min) / range) * height
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${(i * stepX).toFixed(1)} ${y(p).toFixed(1)}`).join(" ")
  const isUp = points[points.length - 1] >= refValue
  const color = isUp ? "#f87171" : "#34d399" // text-red-400 / text-emerald-400，跟全站紅漲綠跌一致
  const refY = y(refValue).toFixed(1)
  return (
    <svg width={width} height={height} className="shrink-0" aria-hidden="true">
      <line x1={0} y1={refY} x2={width} y2={refY} stroke="#52525b" strokeWidth={1} strokeDasharray="2,2" />
      <path d={path} fill="none" stroke={color} strokeWidth={1.5} />
    </svg>
  )
}

export function WatchlistView() {
  const tickers = useWatchlist()
  const [rows, setRows] = useState<Record<string, WatchRow>>({})
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchQuotes = useCallback(async (list: string[], silent = false) => {
    if (list.length === 0) {
      setRows({})
      setLoading(false)
      return
    }
    if (!silent) setLoading(true)
    try {
      const results = await Promise.all(
        list.map(async (ticker) => {
          const [stockRes, intradayRes] = await Promise.all([
            fetch(`/api/stock/${ticker}?period=1mo&interval=1d`),
            fetch(`/api/stock/${ticker}/intraday`),
          ])
          const stock = stockRes.ok ? ((await stockRes.json()) as StockData) : null
          const intraday = intradayRes.ok ? ((await intradayRes.json()) as IntradaySeries) : null
          return [ticker, { stock, intraday }] as const
        })
      )
      setRows(Object.fromEntries(results))
      setLastUpdated(new Date())
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchQuotes(tickers)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tickers.join(","), fetchQuotes])

  // 定期背景刷新（報價/分時中台快取 30 秒 TTL），分頁在背景時暫停，切回前景立刻補刷一次
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
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">自選股</h1>
        <p className="text-xs text-muted-foreground mt-1">
          存在這台電腦的瀏覽器，換裝置或清瀏覽器資料會消失。
          {lastUpdated && <> 更新於 {formatTimeShort(lastUpdated.toISOString())}</>}
        </p>
      </div>

      {tickers.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center border border-dashed border-zinc-800 rounded-lg">
          <Star size={28} className="text-zinc-600" />
          <p className="text-sm text-muted-foreground">
            還沒有自選股。到{" "}
            <Link href="/stock" className="text-sidebar-primary hover:underline">
              個股分析
            </Link>{" "}
            點標題旁的星星加入。
          </p>
        </div>
      ) : (
        <div className="divide-y divide-zinc-800 border-t border-b border-zinc-800">
          {tickers.map((ticker) => {
            const row = rows[ticker]
            const latest = row?.stock?.latest
            const isUp = (latest?.change ?? 0) >= 0
            const points = row?.intraday?.points.map((p) => p.price) ?? []
            const refValue = row?.intraday?.prev_close

            return (
              <div key={ticker} className="group relative flex items-center gap-3 py-3">
                <Link
                  href={`/stock/${ticker}`}
                  className="flex flex-1 items-center gap-3 min-w-0 min-h-11"
                >
                  {/* 名稱 */}
                  <div className="min-w-0 flex-1">
                    {loading && !row ? (
                      <>
                        <Skeleton className="h-4 w-16 bg-zinc-800 mb-1.5" />
                        <Skeleton className="h-3 w-10 bg-zinc-800" />
                      </>
                    ) : (
                      <>
                        <p className="text-base font-semibold text-white truncate">
                          {row?.stock?.name ?? ticker}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">{ticker}</p>
                      </>
                    )}
                  </div>

                  {/* 迷你走勢圖 */}
                  {loading && !row ? (
                    <Skeleton className="h-8 w-22 bg-zinc-800 shrink-0" />
                  ) : refValue != null ? (
                    <Sparkline points={points} refValue={refValue} />
                  ) : (
                    <div className="w-22 shrink-0" />
                  )}

                  {/* 價格 + 漲跌色塊 */}
                  <div className="text-right shrink-0 w-24">
                    {loading && !row ? (
                      <>
                        <Skeleton className="h-4 w-14 bg-zinc-800 mb-1.5 ml-auto" />
                        <Skeleton className="h-5 w-16 bg-zinc-800 ml-auto" />
                      </>
                    ) : latest ? (
                      <>
                        <p className="text-base font-semibold text-white tabular-nums">
                          {latest.price.toLocaleString()}
                        </p>
                        <span
                          className={`inline-block mt-1 px-1.5 py-0.5 rounded text-xs font-medium tabular-nums text-white ${
                            isUp ? "bg-red-500" : "bg-emerald-500"
                          }`}
                        >
                          {fmtChange(latest.change, latest.change_pct)}
                        </span>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">—</p>
                    )}
                  </div>
                </Link>

                <button
                  onClick={() => removeFromWatchlist(ticker)}
                  aria-label={`移除 ${ticker}`}
                  className="flex items-center justify-center h-11 w-11 -mr-2.5 rounded-md text-zinc-600 hover:text-red-400 transition-colors shrink-0"
                >
                  <X size={14} />
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
