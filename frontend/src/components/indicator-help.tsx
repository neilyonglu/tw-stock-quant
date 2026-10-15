import type { ReactNode } from "react"
import { Info } from "lucide-react"

export const INDICATOR_HELP = {
  sma: "SMA 是平均收盤價。SMA20／SMA60 分別平均最近 20／60 根 K 棒；價格在上方只表示高於均價，不代表本根剛突破。看日線是交易日，看 5 分線就是 5 分 K 的根數。",
  rsi: "RSI(14) 比較最近 14 期的漲跌力道，範圍 0–100。常用 70 以上、30 以下觀察超買／超賣；強勢時可以長期在高檔，弱勢時也可能持續低檔。75 不是上漲機率 75%。",
  macd: "MACD 線＝EMA12－EMA26；訊號線是 MACD 的 9 期 EMA，柱狀圖是兩線的差。EMA 較重視近期價格。線在上方／下方是目前位置；真正金叉／死叉須觀察前後兩根是否穿越。零軸上方表示 EMA12 高於 EMA26。",
  volume: "均量線是最近 5／10 根 K 棒的平均成交量，包含本根；用來觀察交易是否比平常活躍，數字單位與來源成交量一致。成交量不是成交金額。",
  ratio: "本頁量比＝本根成交量 ÷ 前 5 根平均成交量，不含本根。1.5 倍是多 50%，0.5 倍是一半；這與券商的盤中累計量比算法可能不同。尚未收完的 K 棒，不宜直接與完整 K 棒比較。",
  patterns: "晨星、錘子線、多頭吞噬等是偏多形狀；黃昏星、上吊線、空頭吞噬等是偏空形狀。本頁只列最近 5 根內的辨識結果；形狀本身不保證反轉，仍要配合前段趨勢與成交量。",
}

export function IndicatorHelp({ label, children }: { label: string; children: ReactNode }) {
  return (
    <details className="min-w-0 flex-1">
      <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 rounded text-xs text-zinc-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 [&::-webkit-details-marker]:hidden">
        <span>{label}</span>
        <Info size={15} aria-hidden="true" className="shrink-0" />
        <span className="sr-only">指標說明</span>
      </summary>
      <p className="mb-3 text-xs leading-relaxed text-zinc-300">{children}</p>
    </details>
  )
}

export function IndicatorGuide() {
  const topics = [
    ["SMA／EMA 均線", INDICATOR_HELP.sma + " EMA 則讓近期價格有較高權重，對變化反應較快。"],
    ["RSI(14)", INDICATOR_HELP.rsi],
    ["MACD(12,26,9)", INDICATOR_HELP.macd],
    ["5／10 期均量", INDICATOR_HELP.volume],
    ["量比", INDICATOR_HELP.ratio],
    ["K 線型態", INDICATOR_HELP.patterns],
  ]
  return (
    <details className="mb-3 rounded-lg border border-zinc-800 bg-zinc-950">
      <summary className="flex min-h-11 cursor-pointer items-center gap-2 px-3 text-sm text-zinc-300 focus-visible:outline-2 focus-visible:outline-emerald-400">
        <Info size={16} aria-hidden="true" />圖表指標怎麼看
      </summary>
      <dl className="grid gap-4 px-3 pb-4 text-xs leading-relaxed md:grid-cols-2">
        {topics.map(([label, description]) => (
          <div key={label}><dt className="mb-1 font-medium text-zinc-100">{label}</dt><dd className="text-zinc-400">{description}</dd></div>
        ))}
      </dl>
    </details>
  )
}
