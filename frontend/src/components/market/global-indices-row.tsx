import type { GlobalIndex } from "@/lib/types"

export function GlobalIndicesRow({ indices }: { indices: GlobalIndex[] }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-md p-4">
      <p className="text-xs text-zinc-500 mb-3">國際指數（判斷開盤情緒的參考）</p>
      <div className="flex flex-wrap gap-x-8 gap-y-2">
        {indices.map((idx) => (
          <div key={idx.name} className="flex items-baseline gap-2">
            <span className="text-sm text-zinc-400">{idx.name}</span>
            <span className="text-sm font-medium tabular-nums text-white">{idx.value.toLocaleString()}</span>
            <span className={`text-xs tabular-nums ${idx.change_pct >= 0 ? "text-red-400" : "text-emerald-400"}`}>
              {idx.change_pct >= 0 ? "+" : ""}{idx.change_pct.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
