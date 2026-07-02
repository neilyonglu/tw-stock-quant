import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: string
  sub?: string
  badge?: {
    text: string
    variant?: "default" | "secondary" | "destructive" | "outline"
    // 蓋掉 variant 預設色，畫面上真的需要紅漲綠跌配色時用（shadcn variant 沒有「綠色」選項）
    className?: string
  }
  valueClassName?: string
  hint?: string
  // 用於非漲跌類的色階指標（例如景氣燈號），用小色點跟「紅漲綠跌」的文字配色做區隔，
  // 避免使用者誤把這個顏色當成漲跌方向。傳入 bg-* 的 Tailwind class。
  dot?: string
}

export function StatCard({ label, value, sub, badge, valueClassName, hint, dot }: StatCardProps) {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardContent className="p-4">
        <p className="text-xs text-zinc-400 mb-1">{label}</p>
        <div className="flex items-baseline gap-2 flex-wrap">
          {dot && <span className={cn("inline-block w-2.5 h-2.5 rounded-full", dot)} />}
          <span className={cn("text-xl font-semibold tabular-nums", valueClassName)}>
            {value}
          </span>
          {sub && <span className="text-sm text-zinc-400 tabular-nums">{sub}</span>}
          {badge && (
            <Badge variant={badge.variant ?? "default"} className={cn("ml-auto text-xs", badge.className)}>
              {badge.text}
            </Badge>
          )}
        </div>
        {hint && (
          <p className="text-xs text-zinc-500 mt-2 leading-snug">{hint}</p>
        )}
      </CardContent>
    </Card>
  )
}
