"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { KlineChart } from "@/components/charts/kline-chart"
import { StatCard } from "@/components/stat-card"
import { SignalBadge } from "@/components/signal-badge"
import { OrderBook } from "@/components/stock/order-book"
import { IntradayTab } from "@/components/stock/intraday-tab"
import { ProfileTab } from "@/components/stock/profile-tab"
import { ChipTab } from "@/components/stock/chip-tab"
import { NewsTab } from "@/components/stock/news-tab"
import type { StockData } from "@/lib/types"
import { Search } from "lucide-react"

// ─── K 線週期 / 區間 ──────────────────────────────────────────────────────────
// 日/週/月：可選資料區間。分鐘線（5/15/30/60分）：Yahoo/yfinance 只給得到近期資料，
// 固定用一個夠用的區間，不額外讓使用者選，避免選了也抓不到資料。

const DAY_PERIODS = [
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
]
const WEEK_PERIODS = [
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "5Y", value: "5y" },
]
const MONTH_PERIODS = [
  { label: "5Y", value: "5y" },
  { label: "10Y", value: "10y" },
  { label: "全部", value: "max" },
]

const INTERVALS = [
  { label: "5分", value: "5m", fixedPeriod: "5d", hint: "分鐘線資料僅涵蓋近 5 個交易日" },
  { label: "15分", value: "15m", fixedPeriod: "5d", hint: "分鐘線資料僅涵蓋近 5 個交易日" },
  { label: "30分", value: "30m", fixedPeriod: "1mo", hint: "分鐘線資料僅涵蓋近 1 個月" },
  { label: "60分", value: "60m", fixedPeriod: "3mo", hint: "分鐘線資料僅涵蓋近 3 個月" },
  { label: "日", value: "1d", periods: DAY_PERIODS, defaultPeriod: "6mo" },
  { label: "週", value: "1wk", periods: WEEK_PERIODS, defaultPeriod: "2y" },
  { label: "月", value: "1mo", periods: MONTH_PERIODS, defaultPeriod: "10y" },
] as const

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

  // K 線型態（mock，見 lib/types.ts CandlePattern 說明）
  for (const p of data.patterns) {
    signals.push({
      level: p.signal === "bullish" ? "positive" : "negative",
      label: `K 線型態：${p.name}`,
      desc: p.signal === "bullish" ? "通常代表偏多訊號" : "通常代表偏空訊號",
    })
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
  const [interval, setIntervalValue] = useState<(typeof INTERVALS)[number]["value"]>("1d")
  const [period, setPeriod] = useState("6mo")
  const [data, setData] = useState<StockData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const activeInterval = INTERVALS.find((iv) => iv.value === interval)!

  const fetchData = useCallback(async (ticker: string, p: string, iv: string) => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`/api/stock/${ticker}?period=${p}&interval=${iv}`, { signal: ctrl.signal })
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
    fetchData(activeTicker, period, interval)
  }, [activeTicker, period, interval, fetchData])

  function handleSearch() {
    const t = tickerInput.trim().replace(/\.TW$/i, "")
    if (t) setActiveTicker(t)
  }

  function handleIntervalChange(value: string) {
    const iv = INTERVALS.find((i) => i.value === value)
    if (!iv) return
    setIntervalValue(iv.value)
    setPeriod("periods" in iv ? iv.defaultPeriod : iv.fixedPeriod)
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

          {/* K 線週期 */}
          <div>
            <p className="text-xs text-zinc-500 mb-2">K 線週期</p>
            <ToggleGroup
              value={[interval]}
              onValueChange={(vals) => { if (vals.length > 0) handleIntervalChange(vals[0]) }}
              className="grid grid-cols-4 gap-0.5"
            >
              {INTERVALS.map(({ label, value }) => (
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

          {/* 時間區間（僅日/週/月可選；分鐘線固定區間） */}
          {"periods" in activeInterval ? (
            <div>
              <p className="text-xs text-zinc-500 mb-2">時間區間</p>
              <ToggleGroup
                value={[period]}
                onValueChange={(vals) => { if (vals.length > 0) setPeriod(vals[0]) }}
                className="grid grid-cols-3 gap-0.5"
              >
                {activeInterval.periods.map(({ label, value }) => (
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
          ) : (
            <p className="text-xs text-zinc-500 leading-snug">{activeInterval.hint}</p>
          )}

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

          {/* 五檔報價 */}
          {latest && (
            <div>
              <p className="text-xs text-zinc-500 mb-2">五檔報價</p>
              <OrderBook ticker={activeTicker} />
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
          <h1 className="text-lg font-semibold text-white">
            {activeTicker}
            {data?.name && <span className="text-zinc-400 font-normal ml-1.5">{data.name}</span>}
          </h1>
          {loading && <Skeleton className="h-6 w-32 bg-zinc-800" />}
          {!loading && latest && (
            <>
              <span className="text-2xl font-bold tabular-nums text-white">
                {latest.price.toLocaleString()}
              </span>
              <span className={`text-sm tabular-nums font-medium ${isUp ? "text-red-400" : "text-emerald-400"}`}>
                {fmtChange(latest.change, latest.change_pct)}
              </span>
              <span className="text-xs text-zinc-500 tabular-nums ml-auto">
                漲停 <span className="text-red-400">{latest.limit_up}</span>　跌停 <span className="text-emerald-400">{latest.limit_down}</span>
              </span>
            </>
          )}
          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>

        <div className="p-4">
          <Tabs defaultValue="intraday">
            <TabsList className="mb-3 bg-zinc-900 border border-zinc-800">
              <TabsTrigger value="intraday">分時</TabsTrigger>
              <TabsTrigger value="chart">K 線圖</TabsTrigger>
              <TabsTrigger value="stats">速查指標</TabsTrigger>
              <TabsTrigger value="chip">籌碼面</TabsTrigger>
              <TabsTrigger value="profile">基本面</TabsTrigger>
              <TabsTrigger value="news">新聞</TabsTrigger>
            </TabsList>

            {/* 分時走勢 */}
            <TabsContent value="intraday">
              <IntradayTab ticker={activeTicker} />
            </TabsContent>

            {/* 圖表 */}
            <TabsContent value="chart" className="space-y-1.5">
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
            </TabsContent>

            {/* 速查 StatCard */}
            <TabsContent value="stats">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {loading ? (
                  [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)
                ) : latest ? (
                  <>
                    <StatCard
                      label="現價 / 漲跌"
                      value={latest.price.toLocaleString()}
                      sub={fmtChange(latest.change, latest.change_pct)}
                      valueClassName={isUp ? "text-red-400" : "text-emerald-400"}
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
            </TabsContent>

            {/* 籌碼面 */}
            <TabsContent value="chip">
              <ChipTab ticker={activeTicker} />
            </TabsContent>

            {/* 基本面 */}
            <TabsContent value="profile">
              <ProfileTab ticker={activeTicker} />
            </TabsContent>

            {/* 新聞 */}
            <TabsContent value="news">
              <NewsTab ticker={activeTicker} name={data?.name} />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}
