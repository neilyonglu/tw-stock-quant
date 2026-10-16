"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { StatCard } from "@/components/stat-card"
import { FundamentalPanel } from "@/components/stock/fundamental-panel"
import type { StockProfile } from "@/lib/types"

export function ProfileTab({ ticker }: { ticker: string }) {
  return <div className="space-y-6"><ProfileSummary key={`summary-${ticker}`} ticker={ticker} /><FundamentalPanel key={ticker} ticker={ticker} /></div>
}

function ProfileSummary({ ticker }: { ticker: string }) {
  const [data, setData] = useState<StockProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const ctrl = new AbortController()
    setLoading(true)
    setData(null)
    setError(null)
    fetch(`/api/stock/${ticker}/profile`, { signal: ctrl.signal })
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) throw new Error(json.error ?? "Unknown error")
        setData(json)
      })
      .catch((e: unknown) => {
        if (e instanceof Error && e.name === "AbortError") return
        setError(e instanceof Error ? e.message : "Failed to load data")
      })
      .finally(() => { if (!ctrl.signal.aborted) setLoading(false) })
    return () => ctrl.abort()
  }, [ticker])

  if (error) {
    return (
      <div className="flex items-center justify-center h-24 text-sm text-muted-foreground">
        暫時無法載入基本面資料（資料服務可能未啟動）
      </div>
    )
  }

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
          label="每股盈餘（近 12 個月）"
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
          value={data.market_cap != null ? `${data.market_cap.toLocaleString()} 億` : "—"}
          hint="公司現在市場上值多少錢，數字越大通常代表越穩定、波動較小"
        />
        <StatCard
          label="股本"
          value={data.shares_outstanding != null ? `${data.shares_outstanding.toFixed(2)} 億股` : "—"}
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

    </div>
  )
}
