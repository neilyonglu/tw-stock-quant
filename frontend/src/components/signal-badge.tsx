import { CheckCircle, AlertTriangle, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"

type SignalLevel = "positive" | "warning" | "negative"

interface SignalBadgeProps {
  level: SignalLevel
  label: string
  desc?: string
}

const icons = {
  positive: CheckCircle,
  warning: AlertTriangle,
  negative: XCircle,
}

const colors = {
  positive: "text-emerald-400",
  warning: "text-amber-400",
  negative: "text-red-400",
}

export function SignalBadge({ level, label, desc }: SignalBadgeProps) {
  const Icon = icons[level]
  return (
    <div className="flex items-start gap-2 py-1.5">
      <Icon size={14} className={cn("mt-0.5 shrink-0", colors[level])} />
      <div>
        <p className="text-sm text-zinc-200 leading-tight">{label}</p>
        {desc && <p className="text-xs text-zinc-500 mt-0.5">{desc}</p>}
      </div>
    </div>
  )
}
