"use client"

import { useCallback, useEffect, useState } from "react"
import { RotateCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { StatCard } from "@/components/stat-card"
import { MarketBanner } from "@/components/market-banner"
import type { BusinessCycleLight, MarketOverviewData } from "@/lib/types"

const LIGHT_COLOR: Record<BusinessCycleLight, string> = {
  red: "text-red-400",
  "yellow-red": "text-amber-400",
  green: "text-emerald-400",
  "yellow-blue": "text-sky-400",
  blue: "text-blue-400",
}

function fmtChange(change: number, suffix = "") {
  const sign = change >= 0 ? "+" : ""
  return `${sign}${change}${suffix}`
}

const BREADTH_ITEMS: Array<{ key: keyof MarketOverviewData["breadth"]; label: string }> = [
  { key: "up", label: "上漲家數" },
  { key: "down", label: "下跌家數" },
  { key: "flat", label: "平盤家數" },
  { key: "limit_up", label: "漲停家數" },
  { key: "limit_down", label: "跌停家數" },
]

export function MarketOverviewView() {
  const [data, setData] = useState<MarketOverviewData | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/market")
      setData(await res.json())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* 標題列 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">台股市場總覽</h1>
          {data && (
            <p className="text-xs text-zinc-500 mt-1">
              資料時間：{new Date(data.updated_at).toLocaleString("zh-TW")}
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-zinc-700"
          onClick={fetchData}
          disabled={loading}
        >
          <RotateCw size={14} className={loading ? "animate-spin" : ""} />
          重新整理
        </Button>
      </div>

      {/* 四個指數卡 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {loading || !data ? (
          [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)
        ) : (
          <>
            <StatCard
              label="加權指數"
              value={data.taiex.value.toLocaleString()}
              sub={`${fmtChange(data.taiex.change)} (${fmtChange(data.taiex.change_pct)}%)`}
              valueClassName={data.taiex.change >= 0 ? "text-emerald-400" : "text-red-400"}
              hint="台股大盤的整體溫度計，反映上市公司平均表現"
            />
            <StatCard
              label="景氣燈號"
              value={data.business_cycle.label}
              valueClassName={LIGHT_COLOR[data.business_cycle.light]}
              hint="國發會每月公布，綠燈代表景氣穩定、藍燈代表景氣轉弱"
            />
            <StatCard
              label="USD/TWD"
              value={data.usdtwd.value.toFixed(2)}
              sub={fmtChange(data.usdtwd.change)}
              valueClassName={data.usdtwd.change >= 0 ? "text-red-400" : "text-emerald-400"}
              hint="台幣貶值（數字變大）時，外資較容易撤出台股"
            />
            <StatCard
              label="美債 10Y"
              value={`${data.us10y.value.toFixed(2)}%`}
              sub={fmtChange(data.us10y.change)}
              valueClassName={data.us10y.change >= 0 ? "text-red-400" : "text-emerald-400"}
              hint="殖利率快速走升，會壓抑高本益比成長股的估值"
            />
          </>
        )}
      </div>

      {/* 三大法人 */}
      <div>
        <p className="text-sm text-zinc-400 mb-2">三大法人今日買賣超（億元）</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {loading || !data ? (
            [...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 bg-zinc-900" />)
          ) : (
            <>
              <StatCard
                label="外資"
                value={`${fmtChange(data.institutional.foreign)} 億`}
                valueClassName={data.institutional.foreign >= 0 ? "text-emerald-400" : "text-red-400"}
                hint="外國大資金今天在買，是好訊號；外資是三大法人中影響力最大的"
              />
              <StatCard
                label="投信"
                value={`${fmtChange(data.institutional.trust)} 億`}
                valueClassName={data.institutional.trust >= 0 ? "text-emerald-400" : "text-red-400"}
                hint="本土基金在買，月底作帳行情前常見投信買超"
              />
              <StatCard
                label="自營商"
                value={`${fmtChange(data.institutional.dealer)} 億`}
                valueClassName={data.institutional.dealer >= 0 ? "text-emerald-400" : "text-red-400"}
                hint="券商自有資金的部位，波動較大、參考性較低"
              />
            </>
          )}
        </div>
      </div>

      {/* 市場廣度 */}
      <div>
        <p className="text-sm text-zinc-400 mb-2">市場廣度</p>
        {loading || !data ? (
          <Skeleton className="h-20 bg-zinc-900" />
        ) : (
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4 flex justify-between">
            {BREADTH_ITEMS.map(({ key, label }) => (
              <div key={key} className="text-center">
                <p className="text-2xl font-semibold tabular-nums text-white">
                  {data.breadth[key]}
                </p>
                <p className="text-xs text-zinc-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 環境結論橫幅 */}
      {loading || !data ? (
        <Skeleton className="h-20 bg-zinc-900" />
      ) : (
        <MarketBanner verdict={data.environment.verdict} intensity={data.environment.intensity} />
      )}
    </div>
  )
}
