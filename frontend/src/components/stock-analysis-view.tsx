"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { KlineChart, type Candle, type VolumeBar, type TimeValue, type MacdPayload } from "@/components/charts/kline-chart"
import { StatCard } from "@/components/stat-card"
import { SignalBadge } from "@/components/signal-badge"
import { Search } from "lucide-react"

// ─── Types ────────────────────────────────────────────────────────────────────

interface LatestMetrics {
  price: number
  change: number
  change_pct: number
  rsi: number
  macd_crossover: "golden" | "dead"
  volume_ratio: number
}

interface StockData {
  ticker: string
  candles: Candle[]
  volume: VolumeBar[]
  sma20: TimeValue[]
  sma60: TimeValue[]
  rsi: TimeValue[]
  macd: MacdPayload
  latest: LatestMetrics
}

const PERIODS = [
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
]

// ─── Signals helper ───────────────────────────────────────────────────────────

function buildSignals(data: StockData) {
  const { latest, candles, sma20 } = data
  const signals: Array<{ level: "positive" | "warning" | "negative"; label: string; desc: string }> = []

  // SMA20 position
  const lastClose = candles[candles.length - 1]?.close
  const lastSma20 = sma20[sma20.length - 1]?.value
  if (lastClose != null && lastSma20 != null) {
    if (lastClose > lastSma20) {
      signals.push({ level: "positive", label: "站上 SMA20", desc: `收盤 ${lastClose} > 均線 ${lastSma20.toFixed(0)}` })
    } else {
      signals.push({ level: "negative", label: "跌破 SMA20", desc: `收盤 ${lastClose} < 均線 ${lastSma20.toFixed(0)}` })
    }
  }

  // MACD
  if (latest.macd_crossover === "golden") {
    signals.push({ level: "positive", label: "MACD 金叉", desc: "動能轉多，MACD 線高於訊號線" })
  } else {
    signals.push({ level: "negative", label: "MACD 死叉", desc: "動能偏空，MACD 線低於訊號線" })
  }

  // RSI
  if (latest.rsi > 70) {
    signals.push({ level: "warning", label: `RSI ${latest.rsi} 超買`, desc: "RSI > 70，短期可能拉回" })
  } else if (latest.rsi < 30) {
    signals.push({ level: "warning", label: `RSI ${latest.rsi} 超賣`, desc: "RSI < 30，短期可能反彈" })
  } else {
    signals.push({ level: "positive", label: `RSI ${latest.rsi} 健康`, desc: "RSI 介於 30–70，動能正常" })
  }

  // Volume
  if (latest.volume_ratio >= 1.5) {
    signals.push({ level: "positive", label: `量增 ${latest.volume_ratio}x`, desc: "今日成交量顯著放大" })
  } else if (latest.volume_ratio < 0.7) {
    signals.push({ level: "warning", label: `量縮 ${latest.volume_ratio}x`, desc: "今日成交量明顯萎縮" })
  }

  return signals
}

// ─── Price display helpers ────────────────────────────────────────────────────

function fmtChange(change: number, pct: number) {
  const sign = change >= 0 ? "+" : ""
  return `${sign}${change.toFixed(2)} (${sign}${pct.toFixed(2)}%)`
}

// ─── Main component ───────────────────────────────────────────────────────────

export function StockAnalysisView({ initialTicker }: { initialTicker: string }) {
  const [tickerInput, setTickerInput] = useState(initialTicker)
  const [activeTicker, setActiveTicker] = useState(initialTicker)
  const [period, setPeriod] = useState("6mo")
  const [data, setData] = useState<StockData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const fetchData = useCallback(async (ticker: string, p: string) => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`/api/stock/${ticker}?period=${p}`, { signal: ctrl.signal })
      const json = await res.json()
      if (!res.ok) throw new Error(json.error ?? "Unknown error")
      setData(json)
    } catch (e: unknown) {
      if (e instanceof Error && e.name === "AbortError") return
      setError(e instanceof Error ? e.message : "Failed to load data")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(activeTicker, period)
  }, [activeTicker, period, fetchData])

  function handleSearch() {
    const t = tickerInput.trim().replace(/\.TW$/i, "")
    if (t) setActiveTicker(t)
  }

  const latest = data?.latest
  const isUp = (latest?.change ?? 0) >= 0

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── 左側控制欄 ── */}
      <aside className="w-56 shrink-0 border-r border-zinc-800 flex flex-col bg-zinc-950 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* 搜尋 */}
          <div>
            <p className="text-xs text-zinc-500 mb-2">股票代碼</p>
            <div className="flex gap-1.5">
              <Input
                value={tickerInput}
                onChange={(e) => setTickerInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="2330"
                className="bg-zinc-900 border-zinc-700 text-sm h-8"
              />
              <Button size="sm" variant="outline" className="h-8 px-2 border-zinc-700" onClick={handleSearch}>
                <Search size={14} />
              </Button>
            </div>
          </div>

          {/* 時間區間 */}
          <div>
            <p className="text-xs text-zinc-500 mb-2">時間區間</p>
            <ToggleGroup
              value={[period]}
              onValueChange={(vals) => { if (vals.length > 0) setPeriod(vals[0]) }}
              className="grid grid-cols-4 gap-0.5"
            >
              {PERIODS.map(({ label, value }) => (
                <ToggleGroupItem
                  key={value}
                  value={value}
                  className="text-xs h-7 aria-pressed:bg-zinc-700 aria-pressed:text-white border border-zinc-800"
                >
                  {label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>

          {/* 技術訊號 */}
          {data && (
            <div>
              <p className="text-xs text-zinc-500 mb-2">技術訊號</p>
              <div className="space-y-0.5">
                {buildSignals(data).map((s, i) => (
                  <SignalBadge key={i} level={s.level} label={s.label} desc={s.desc} />
                ))}
              </div>
            </div>
          )}
          {loading && (
            <div className="space-y-2 pt-1">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full bg-zinc-800" />
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* ── 主圖區 ── */}
      <main className="flex-1 overflow-y-auto">
        {/* 標題列 */}
        <div className="px-6 py-4 border-b border-zinc-800 flex items-baseline gap-3">
          <h1 className="text-lg font-semibold text-white">{activeTicker}</h1>
          {loading && <Skeleton className="h-6 w-32 bg-zinc-800" />}
          {!loading && latest && (
            <>
              <span className="text-2xl font-bold tabular-nums text-white">
                {latest.price.toLocaleString()}
              </span>
              <span className={`text-sm tabular-nums font-medium ${isUp ? "text-emerald-400" : "text-red-400"}`}>
                {fmtChange(latest.change, latest.change_pct)}
              </span>
            </>
          )}
          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>

        <div className="p-4 space-y-4">
          {/* 圖表 */}
          {loading && (
            <div className="space-y-1.5">
              <Skeleton className="h-125 w-full bg-zinc-900" />
              <Skeleton className="h-30 w-full bg-zinc-900" />
              <Skeleton className="h-30 w-full bg-zinc-900" />
              <Skeleton className="h-30 w-full bg-zinc-900" />
            </div>
          )}
          {!loading && data && (
            <KlineChart
              candles={data.candles}
              volume={data.volume}
              sma20={data.sma20}
              sma60={data.sma60}
              rsi={data.rsi}
              macd={data.macd}
            />
          )}
          {!loading && error && (
            <div className="h-215 flex items-center justify-center text-zinc-500">
              無法載入 {activeTicker} 的資料，請確認代碼是否正確
            </div>
          )}

          {/* 速查 StatCard */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {loading ? (
              [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)
            ) : latest ? (
              <>
                <StatCard
                  label="現價 / 漲跌"
                  value={latest.price.toLocaleString()}
                  sub={fmtChange(latest.change, latest.change_pct)}
                  valueClassName={isUp ? "text-emerald-400" : "text-red-400"}
                  hint="台股漲跌停限制 ±10%，無法保證以目標價成交"
                />
                <StatCard
                  label="RSI (14)"
                  value={latest.rsi.toString()}
                  badge={
                    latest.rsi > 70
                      ? { text: "超買", variant: "destructive" }
                      : latest.rsi < 30
                      ? { text: "超賣", variant: "outline" }
                      : { text: "健康", variant: "default" }
                  }
                  hint="RSI < 30 超賣可能反彈；> 70 超買可能拉回；30–70 動能健康"
                />
                <StatCard
                  label="MACD 狀態"
                  value={latest.macd_crossover === "golden" ? "金叉" : "死叉"}
                  badge={
                    latest.macd_crossover === "golden"
                      ? { text: "多頭", variant: "default" }
                      : { text: "空頭", variant: "destructive" }
                  }
                  hint="MACD 金叉代表短期動能轉強，死叉代表動能轉弱"
                />
                <StatCard
                  label="量比（vs 5 日均量）"
                  value={`${latest.volume_ratio.toFixed(2)}x`}
                  valueClassName={latest.volume_ratio >= 1.5 ? "text-emerald-400" : undefined}
                  hint="量比 ≥ 1.5x 表示今日放量，是突破或下跌的重要確認訊號"
                />
              </>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  )
}
