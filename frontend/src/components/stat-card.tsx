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
  }
  valueClassName?: string
  hint?: string
}

export function StatCard({ label, value, sub, badge, valueClassName, hint }: StatCardProps) {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardContent className="p-4">
        <p className="text-xs text-zinc-400 mb-1">{label}</p>
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className={cn("text-xl font-semibold tabular-nums", valueClassName)}>
            {value}
          </span>
          {sub && <span className="text-sm text-zinc-400 tabular-nums">{sub}</span>}
          {badge && (
            <Badge variant={badge.variant ?? "default"} className="ml-auto text-xs">
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
