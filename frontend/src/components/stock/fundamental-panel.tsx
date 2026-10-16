"use client"

import { useEffect, useState } from "react"
import { StatCard } from "@/components/stat-card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { FundamentalAnalysis, FundamentalRule } from "@/lib/types"
import { formatDate, formatDateTime } from "@/lib/utils"

const signalLabels: Record<string, string> = {
  positive_roa: "年度資產報酬為正", positive_cfo: "年度營業現金流為正", improving_roa: "資產報酬率提高",
  cash_exceeds_profit: "營業現金流高於淨利", lower_leverage: "長期負債比下降", improving_liquidity: "流動比率提高",
  no_equity_issued: "年度未發行普通股", improving_margin: "毛利率提高", improving_turnover: "資產周轉率提高",
}

function verdict(rule: FundamentalRule | undefined): string {
  if (!rule) return "資料不足"
  if (rule.status === "pending_update") return "資料待更新，暫不判定"
  if (rule.status === "needs_review") return "數值待核對，暫不判定"
  if (rule.condition_met == null) return "資料不足，暫不判定"
  return rule.condition_met ? "研究條件符合門檻" : "研究條件未符合門檻"
}

export function FundamentalPanel({ ticker }: { ticker: string }) {
  const [data, setData] = useState<FundamentalAnalysis | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const ctrl = new AbortController()
    setData(null)
    setError(false)
    fetch(`/api/stock/${ticker}/fundamentals`, { signal: ctrl.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("unavailable")
        const result: FundamentalAnalysis = await response.json()
        if (!result.rules?.length || result.ticker !== ticker) throw new Error("invalid response")
        if (!ctrl.signal.aborted) setData(result)
      })
      .catch(() => { if (!ctrl.signal.aborted) setError(true) })
    return () => ctrl.abort()
  }, [ticker, attempt])

  if (error) return <section aria-label="基本面研究" className="rounded-lg border border-zinc-800 p-4 text-sm">
    <p role="alert" className="text-zinc-400">暫時無法載入財報與營收，尚無法計算基本面條件。</p>
    <Button variant="outline" className="mt-3 min-h-11" onClick={() => setAttempt((value) => value + 1)}>重新載入基本面</Button>
  </section>
  if (!data) return <p role="status" className="rounded-lg border border-zinc-800 p-4 text-sm text-zinc-400">正在載入財報與營收，首次查詢可能需要較久時間…</p>

  const eps = data.rules.find((rule) => rule.id === "eps_positive_four_quarters")
  const roe = data.rules.find((rule) => rule.id === "roe_ttm")
  const revenue = data.rules.find((rule) => rule.id === "revenue_yoy_three_months")
  const fscore = data.rules.find((rule) => rule.id === "piotroski_f_score")
  const rows = data.monthly_revenue ?? []
  const latestMonth = rows.at(-1)?.month
  const supplement = fscore?.value?.inputs.current.supplement
  const quality = data.quality ?? {}
  const pending = Object.values(quality).some((item) => item.status === "pending_update")
  const tableLabels: Record<string, string> = { income_statement: "損益表", balance_sheet: "資產負債表", cash_flow: "現金流量表", monthly_revenue: "月營收" }

  return <section aria-labelledby="fundamental-heading" className="space-y-4">
    <div>
      <h3 id="fundamental-heading" className="font-medium text-zinc-100">基本面研究</h3>
      <p className="mt-1 text-xs leading-relaxed text-zinc-400">來源：FinMind。條件符合度僅供研究，尚未完成全面驗證，不代表已通過選股或買進建議。</p>
      {pending && <p role="status" className="mt-2 rounded-md border border-amber-800/60 bg-amber-950/20 p-3 text-sm text-amber-300">部分財報落後已知公告。以下顯示實際使用期間，受影響條件暫不判定。</p>}
    </div>
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <StatCard label="ROE（近四季）" value={roe?.value ? `${roe.value.percent.toFixed(2)}%` : "—"}
        sub={roe?.value ? `截至 ${formatDate(roe.value.periods.at(-1) ?? "")}` : undefined}
        hint={`${verdict(roe)}；門檻 > 12%`} help="近四季合併本期淨利 ÷ 期初與期末平均合併權益。衡量公司使用股東投入資金創造獲利的能力；本版不是單季數字乘四，與採歸母或平均季末權益的平台可能不同。" />
      <StatCard label="Piotroski F-score" value={fscore?.value?.score != null ? `${fscore.value.score} / 9` : "—"}
        sub={fscore?.value ? `${fscore.value.year} 年度 · 可計算 ${fscore.value.known_signals} 項` : undefined}
        hint={`${verdict(fscore)}；完整總分門檻 ≥ 6`} help="以獲利、現金流、槓桿、流動性、普通股發行與經營效率九項財務訊號各計一分。九項資料齊備才計總分；可計算七項不是七分。採 IFRS 研究口徑，不能當成獲利保證。" />
    </div>
    <div className="rounded-lg border border-zinc-800 p-4">
      <h4 className="text-sm text-zinc-200">最近四季每股盈餘（EPS）</h4>
      <p className="mt-1 text-xs text-zinc-400">{verdict(eps)}；四季均須大於 0，與上方近 12 個月 EPS 卡片口徑不同。</p>
      {eps?.value ? <dl className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">{eps.value.map((item) => <div key={item.period}>
        <dt className="text-xs text-zinc-400">{formatDate(item.period)}</dt><dd className="mt-1 text-lg tabular-nums text-zinc-100">{item.eps.toFixed(2)} <span className="text-xs text-zinc-400">元</span></dd>
      </div>)}</dl> : <p className="mt-3 text-sm text-zinc-400">尚無四個連續季度的完整 EPS。</p>}
    </div>
    <details className="rounded-lg border border-zinc-800 px-4">
      <summary className="flex min-h-11 cursor-pointer items-center text-sm text-zinc-200">查看 F-score 九項訊號</summary>
      {fscore?.value ? <ul className="space-y-2 pb-4 text-sm">{fscore.value.signals.map((signal) => <li key={signal.id} className="flex justify-between gap-3 border-t border-zinc-800 pt-2">
        <span className="text-zinc-300">{signalLabels[signal.id] ?? "財務訊號"}</span><span className="shrink-0 text-zinc-400">{signal.passed == null ? "缺資料" : signal.passed ? "符合" : "未符合"}</span>
      </li>)}</ul> : <p className="pb-4 text-sm text-zinc-400">此股票目前缺少可用資料，或不適用一般產業版本。</p>}
    </details>
    <div>
      <h4 className="text-sm text-zinc-200">近六個月營收 {latestMonth && <span className="text-xs text-zinc-400">· 截至 {formatDate(latestMonth)}</span>}</h4>
      <p className="my-2 text-xs text-zinc-400">{verdict(revenue)}；最近三個月的年增率均須大於 0%。</p>
      {rows.length ? <Table><TableHeader><TableRow className="border-zinc-800"><TableHead>月份</TableHead><TableHead className="text-right">營收（億元）</TableHead><TableHead className="text-right">年增率</TableHead></TableRow></TableHeader>
        <TableBody>{rows.map((row) => <TableRow key={row.month} className="border-zinc-800"><TableCell className="text-zinc-300">{formatDate(row.month)}</TableCell>
          <TableCell className="text-right tabular-nums">{row.revenue != null ? (row.revenue / 1e8).toLocaleString("zh-TW", { maximumFractionDigits: 2, minimumFractionDigits: 2 }) : "—"}</TableCell>
          <TableCell className={`text-right tabular-nums ${row.yoy == null ? "text-zinc-400" : row.yoy >= 0 ? "text-red-400" : "text-emerald-400"}`}>{row.yoy != null ? `${row.yoy >= 0 ? "+" : ""}${row.yoy.toFixed(2)}%` : "—"}</TableCell>
        </TableRow>)}</TableBody></Table> : <p className="text-sm text-zinc-400">暫無可用月營收，未以示範資料替代。</p>}
      <p className="mt-2 text-xs leading-relaxed text-zinc-400">年增率比較去年同月；去年同月缺值或為零時顯示 —。營收月份依實際所屬年月，並非資料入庫日期。</p>
    </div>
    <details className="rounded-lg border border-zinc-800 px-4">
      <summary className="flex min-h-11 cursor-pointer items-center text-sm text-zinc-200">資料來源、期間與限制</summary>
      <div className="space-y-2 pb-4 text-xs leading-relaxed text-zinc-400">
        {Object.entries(quality).map(([name, item]) => <p key={name}>{tableLabels[name] ?? "資料"}：{item.source ?? "來源暫無資料"}{item.latest_period ? `，期間至 ${formatDate(item.latest_period)}` : ""}{item.fetched_at ? `，抓取 ${formatDateTime(item.fetched_at)}` : ""}。</p>)}
        {supplement ? <p>F-score 長債與普通股發行使用 <a className="text-blue-400 underline" href={supplement.source_url} target="_blank" rel="noreferrer">{supplement.year} 年官方合併財報人工核對資料</a>，核對日 {formatDate(supplement.reviewed_on)}。長債含非流動公司債、借款及租賃，排除一年內到期部分。只適用已核對股票及年度，尚非全市場自動更新。</p> : <p>尚無此股票／年度的完整長債與普通股發行核對紀錄，相關訊號保持缺資料。</p>}
        <p>抓取時間很新不代表財報已更新；目前僅有限人工核對，沒有完整追蹤所有官方公告。資料有差異或落後時，暫不給出已驗證合格結論。</p>
      </div>
    </details>
  </section>
}
