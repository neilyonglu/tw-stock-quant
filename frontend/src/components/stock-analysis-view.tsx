"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { Skeleton } from "@/components/ui/skeleton"
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
import { TickerSearch } from "@/components/ticker-search"
import type { StockData } from "@/lib/types"
import { SearchX, Star } from "lucide-react"
import { useWatchlist, toggleWatchlist } from "@/lib/watchlist"
import { formatTimeShort } from "@/lib/utils"
import { buildIndicatorSignals, describeRsi, describeVolumeRatio, getIndicatorReadings } from "@/lib/indicator-summary"
import { INDICATOR_HELP, IndicatorGuide } from "@/components/indicator-help"

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

// ─── Price display helpers ────────────────────────────────────────────────────

function fmtChange(change: number, pct: number) {
  const sign = change >= 0 ? "+" : ""
  return `${sign}${change.toFixed(2)} (${sign}${pct.toFixed(2)}%)`
}

// ─── Main component ───────────────────────────────────────────────────────────

export function StockAnalysisView({ initialTicker }: { initialTicker: string }) {
  const [activeTicker, setActiveTicker] = useState(initialTicker)
  const [interval, setIntervalValue] = useState<(typeof INTERVALS)[number]["value"]>("1d")
  const [period, setPeriod] = useState("6mo")
  const [data, setData] = useState<StockData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [staleAdjust, setStaleAdjust] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const watchlist = useWatchlist()
  const inWatchlist = watchlist.includes(activeTicker)

  const activeInterval = INTERVALS.find((iv) => iv.value === interval)!
  // 分鐘線資料跟中台五檔/分時快取同週期（30 秒 TTL），日/週/月線跟中台 K 線快取同週期（60 秒 TTL）
  const refreshMs = activeInterval.value.endsWith("m") ? 30_000 : 60_000

  const fetchData = useCallback(async (ticker: string, p: string, iv: string, silent = false) => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    if (!silent) {
      setLoading(true)
      // 換代碼/週期時立刻清掉舊資料——不然轉圈的當下，標題列還會顯示上一支股票的
      // 名稱/價格，看起來像新代碼查到了舊資料。背景靜默刷新（silent）不清，避免每次
      // 自動刷新都閃一下。
      setData(null)
      setError(null)
      setStaleAdjust(false)
    }

    try {
      const res = await fetch(`/api/stock/${ticker}?period=${p}&interval=${iv}`, { signal: ctrl.signal })
      const json = await res.json()
      if (!res.ok) {
        setStaleAdjust(json.stale_adjust === true)
        setData(null)
        throw new Error(json.error ?? "Unknown error")
      }
      setData(json)
      setError(null)
      setStaleAdjust(false)
      setLastUpdated(new Date())
    } catch (e: unknown) {
      if (e instanceof Error && e.name === "AbortError") return
      setError(e instanceof Error ? e.message : "Failed to load data")
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(activeTicker, period, interval)
  }, [activeTicker, period, interval, fetchData])

  // 定期背景刷新：分頁在背景時暫停，切回前景立刻補刷一次
  useEffect(() => {
    function tick() {
      if (document.hidden) return
      fetchData(activeTicker, period, interval, true)
    }
    const timer = setInterval(tick, refreshMs)
    function onVisible() {
      if (!document.hidden) tick()
    }
    document.addEventListener("visibilitychange", onVisible)
    return () => {
      clearInterval(timer)
      document.removeEventListener("visibilitychange", onVisible)
    }
  }, [activeTicker, period, interval, refreshMs, fetchData])

  function handleIntervalChange(value: string) {
    const iv = INTERVALS.find((i) => i.value === value)
    if (!iv) return
    setIntervalValue(iv.value)
    setPeriod("periods" in iv ? iv.defaultPeriod : iv.fixedPeriod)
  }

  const latest = data?.latest
  const isUp = (latest?.change ?? 0) >= 0
  const readings = data ? getIndicatorReadings(data) : null
  const macdDiff = readings?.macdLine != null && readings.macdSignal != null
    ? readings.macdLine - readings.macdSignal : null
  const barUnit = interval === "1d" ? "1 個交易日" : interval === "1wk" ? "1 週"
    : interval === "1mo" ? "1 個月" : `${parseInt(interval)} 分鐘`

  return (
    <div className="flex flex-col md:flex-row md:h-screen md:overflow-hidden">
      {/* ── 左側控制欄（手機版排在主圖區下方）── */}
      <aside className="order-2 md:order-1 md:w-56 md:shrink-0 border-t md:border-t-0 md:border-r border-zinc-800 flex flex-col bg-zinc-950 md:overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* 搜尋 */}
          <div>
            <label htmlFor="ticker-input" className="text-xs text-muted-foreground mb-2 block">股票代碼</label>
            <TickerSearch id="ticker-input" onSelect={(t) => setActiveTicker(t)} placeholder="2330 或名稱關鍵字" />
          </div>

          {/* K 線週期 */}
          <div>
            <p className="text-xs text-muted-foreground mb-2">K 線週期</p>
            <ToggleGroup
              value={[interval]}
              onValueChange={(vals) => { if (vals.length > 0) handleIntervalChange(vals[0]) }}
              className="grid grid-cols-4 gap-1"
            >
              {INTERVALS.map(({ label, value }) => (
                <ToggleGroupItem
                  key={value}
                  value={value}
                  className="text-xs h-11 aria-pressed:bg-zinc-700 aria-pressed:text-white border border-zinc-800"
                >
                  {label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>

          {/* 時間區間（僅日/週/月可選；分鐘線固定區間） */}
          {"periods" in activeInterval ? (
            <div>
              <p className="text-xs text-muted-foreground mb-2">時間區間</p>
              <ToggleGroup
                value={[period]}
                onValueChange={(vals) => { if (vals.length > 0) setPeriod(vals[0]) }}
                className="grid grid-cols-3 gap-1"
              >
                {activeInterval.periods.map(({ label, value }) => (
                  <ToggleGroupItem
                    key={value}
                    value={value}
                    className="text-xs h-11 aria-pressed:bg-zinc-700 aria-pressed:text-white border border-zinc-800"
                  >
                    {label}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-muted-foreground leading-snug">{activeInterval.hint}</p>
              <button
                onClick={() => setPeriod(period === "1d" ? activeInterval.fixedPeriod : "1d")}
                aria-pressed={period === "1d"}
                className="shrink-0 text-xs h-11 px-3 rounded-md border border-zinc-800 aria-pressed:bg-zinc-700 aria-pressed:text-white text-zinc-400 hover:text-white transition-colors"
              >
                今日
              </button>
            </div>
          )}

          {/* 技術訊號 */}
          {data && (
            <div>
              <p className="text-xs text-muted-foreground mb-2">技術訊號</p>
              <div className="space-y-0.5">
                {buildIndicatorSignals(data).map((s, i) => (
                  <SignalBadge key={i} level={s.level} label={s.label} desc={s.desc} />
                ))}
              </div>
              {data.patterns.length === 0 && (
                <p className="text-xs text-muted-foreground mt-2 leading-snug">
                  最近 5 根 K 棒沒有出現晨星、錘子線、吞噬等型態，所以這裡只有均線／MACD／RSI／量能訊號。
                </p>
              )}
            </div>
          )}

          {/* 五檔報價 */}
          {latest && (
            <div>
              <p className="text-xs text-muted-foreground mb-2">五檔報價</p>
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
      <main className="order-1 md:order-2 flex-1 md:overflow-y-auto">
        {/* 標題列 */}
        <div className="px-6 py-4 border-b border-zinc-800 flex items-baseline gap-3">
          <h1 className="text-lg font-semibold text-white">
            {activeTicker}
            {data?.name && <span className="text-zinc-400 font-normal ml-1.5">{data.name}</span>}
          </h1>
          {!error && (
            <button
              onClick={() => toggleWatchlist(activeTicker)}
              aria-label={inWatchlist ? "移出自選股" : "加入自選股"}
              aria-pressed={inWatchlist}
              className="flex items-center justify-center h-11 w-11 -mx-2.5 rounded-md text-zinc-400 hover:text-amber-400 transition-colors"
            >
              <Star size={18} className={inWatchlist ? "fill-amber-400 text-amber-400" : ""} />
            </button>
          )}
          {loading && <Skeleton className="h-6 w-32 bg-zinc-800" />}
          {!loading && latest && (
            <>
              <span className="text-2xl font-bold tabular-nums text-white">
                {latest.price.toLocaleString()}
              </span>
              <span className={`text-sm tabular-nums font-medium ${isUp ? "text-red-400" : "text-emerald-400"}`}>
                {fmtChange(latest.change, latest.change_pct)}
              </span>
              <span className="text-xs text-muted-foreground tabular-nums ml-auto">
                漲停 <span className="text-red-400">{latest.limit_up ?? "—"}</span>　跌停 <span className="text-emerald-400">{latest.limit_down ?? "—"}</span>
              </span>
            </>
          )}
          {!error && lastUpdated && (
            <span className="text-xs text-muted-foreground tabular-nums">
              更新於 {formatTimeShort(lastUpdated.toISOString())}
            </span>
          )}
        </div>

        {error ? (
          <div className="flex flex-col items-center justify-center gap-3 py-24 text-center px-6">
            <SearchX size={32} className="text-zinc-600" />
            <p role="alert" className="text-sm text-zinc-200">{error}</p>
            <p className="text-xs text-muted-foreground">{staleAdjust ? "已隱藏舊價格與指標，資料恢復後會自動更新。" : "可以到左側重新輸入股票代碼再試一次"}</p>
          </div>
        ) : (
        <div className="p-4">
          <p className="mb-3 text-xs leading-relaxed text-zinc-400" aria-live="polite">
            目前：{activeInterval.label} K，每根代表 {barUnit}。指標期數以 K 棒計算，SMA20 就是 20 根，不一定是 20 日。
            {data && ` 本次載入 ${data.candles.length} 根；資料不足或無有效數值時顯示「—」。`}
          </p>
          <Tabs defaultValue="intraday">
            <div className="overflow-x-auto mb-3">
              <TabsList className="bg-zinc-900 border border-zinc-800 w-max">
                <TabsTrigger value="intraday">分時</TabsTrigger>
                <TabsTrigger value="chart">K 線圖</TabsTrigger>
                <TabsTrigger value="stats">速查指標</TabsTrigger>
                <TabsTrigger value="chip">籌碼面</TabsTrigger>
                <TabsTrigger value="profile">基本面</TabsTrigger>
                <TabsTrigger value="news">新聞</TabsTrigger>
              </TabsList>
            </div>

            {/* 分時走勢 */}
            <TabsContent value="intraday">
              <IntradayTab ticker={activeTicker} />
            </TabsContent>

            {/* 圖表 */}
            <TabsContent value="chart" className="space-y-1.5">
              <IndicatorGuide />
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
                  volumeSma5={data.volume_sma5}
                  volumeSma10={data.volume_sma10}
                  rsi={data.rsi}
                  macd={data.macd}
                  kd={data.kd}
                  atr14={data.atr14}
                />
              )}
            </TabsContent>

            {/* 速查 StatCard */}
            <TabsContent value="stats">
              <p className="mb-3 text-xs leading-relaxed text-zinc-400">點指標名稱旁的 ⓘ 查看說明；最新 K 棒可能尚未收完，成交量需等收完後再比較。</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {loading ? (
                  [...Array(10)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)
                ) : latest && readings ? (
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
                      value={readings.rsi?.toFixed(1) ?? "—"}
                      hint={describeRsi(readings.rsi)}
                      help={INDICATOR_HELP.rsi}
                    />
                    <StatCard
                      label="MACD 線的位置"
                      value={macdDiff == null ? "—" : macdDiff > 0 ? "線在上方" : macdDiff < 0 ? "線在下方" : "兩線重合"}
                      hint={macdDiff == null ? "資料不足或無有效數值，暫不判讀" : `MACD ${readings.macdLine?.toFixed(2)}／訊號線 ${readings.macdSignal?.toFixed(2)}；位置不代表本根剛發生交叉`}
                      help={INDICATOR_HELP.macd}
                    />
                    <StatCard
                      label="量比（前 5 根）"
                      value={readings.volumeRatio == null ? "—" : `${readings.volumeRatio.toFixed(2)} 倍`}
                      hint={describeVolumeRatio(readings.volumeRatio)}
                      help={INDICATOR_HELP.ratio}
                    />
                    <StatCard label="SMA20" value={readings.sma20?.toFixed(2) ?? "—"}
                      hint={readings.sma20 == null ? "需至少 20 根有效 K 棒" : "最近 20 根的平均收盤價"} help={INDICATOR_HELP.sma} />
                    <StatCard label="KD (9,3,3)" value={readings.k == null || readings.d == null ? "—" : `K ${readings.k.toFixed(1)} / D ${readings.d.toFixed(1)}`}
                      hint={readings.k == null || readings.d == null ? "需至少 9 根有效 K 棒" : "80／20 為常用高低檔參考，不保證反轉"} help={INDICATOR_HELP.kd} />
                    <StatCard label="ATR (14)" value={readings.atr14 == null ? "—" : `${readings.atr14.toFixed(2)} 元`}
                      hint={readings.atr14 == null ? "需至少 15 根有效 K 棒" : "近期真實波動幅度，不表示漲跌方向"} help={INDICATOR_HELP.atr} />
                    <StatCard label="SMA60" value={readings.sma60?.toFixed(2) ?? "—"}
                      hint={readings.sma60 == null ? "需至少 60 根有效 K 棒" : "最近 60 根的平均收盤價"} help={INDICATOR_HELP.sma} />
                    <StatCard label="5 期均量" value={readings.volumeSma5?.toLocaleString("zh-TW", { maximumFractionDigits: 0 }) ?? "—"}
                      hint="最近 5 根平均成交量，包含本根" help={INDICATOR_HELP.volume} />
                    <StatCard label="10 期均量" value={readings.volumeSma10?.toLocaleString("zh-TW", { maximumFractionDigits: 0 }) ?? "—"}
                      hint="最近 10 根平均成交量，包含本根" help={INDICATOR_HELP.volume} />
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
        )}
      </main>
    </div>
  )
}
