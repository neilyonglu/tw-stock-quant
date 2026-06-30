import { cn } from "@/lib/utils"
import type { MarketEnvironment, OperationIntensity } from "@/lib/types"

// 台股慣例：紅漲綠跌，多頭（看漲）用紅、空頭（看跌）用綠
const STYLES: Record<MarketEnvironment, { border: string; text: string }> = {
  多頭: { border: "border-l-red-500", text: "text-red-400" },
  盤整: { border: "border-l-amber-500", text: "text-amber-400" },
  空頭: { border: "border-l-emerald-500", text: "text-emerald-400" },
}

interface MarketBannerProps {
  verdict: MarketEnvironment
  intensity: OperationIntensity
}

export function MarketBanner({ verdict, intensity }: MarketBannerProps) {
  const style = STYLES[verdict]
  return (
    <div
      className={cn(
        "border-l-4 bg-zinc-900 border border-zinc-800 rounded-md px-5 py-4",
        style.border
      )}
    >
      <p className="text-xs text-zinc-500 mb-1">總體環境結論</p>
      <p className="text-lg font-semibold text-white">
        市場環境：<span className={style.text}>{verdict}</span>
        <span className="text-zinc-600 mx-3">|</span>
        建議操作強度：<span className={style.text}>{intensity}</span>
      </p>
    </div>
  )
}
