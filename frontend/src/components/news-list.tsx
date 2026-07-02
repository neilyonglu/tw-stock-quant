import { Newspaper } from "lucide-react"
import type { NewsItem } from "@/lib/types"
import { formatTimeShort } from "@/lib/utils"

// 個股新聞跟大盤新聞快訊共用，都是 NewsItem[] 形狀
export function NewsList({ items }: { items: NewsItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-zinc-500 py-6 text-center">目前沒有相關新聞</p>
  }
  return (
    <div className="divide-y divide-zinc-800">
      {items.map((item, i) => (
        <div key={i} className="flex items-start gap-3 py-3">
          <Newspaper size={14} className="text-zinc-500 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm text-zinc-200 leading-snug">{item.title}</p>
            <p className="text-xs text-zinc-500 mt-1">{item.source} · {formatTimeShort(item.time)}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
