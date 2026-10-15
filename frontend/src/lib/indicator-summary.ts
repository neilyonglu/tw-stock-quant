import type { StockData, TimeValue } from "./types"

export type IndicatorSignal = {
  level: "positive" | "warning" | "negative" | "neutral"
  label: string
  desc: string
}

function currentValue(series: TimeValue[], time: TimeValue["time"] | undefined) {
  const point = series.at(-1)
  return point && point.time === time && Number.isFinite(point.value) ? point.value : null
}

export function getIndicatorReadings(data: StockData) {
  const time = data.candles.at(-1)?.time
  const baseline = data.volume.slice(-6, -1).reduce((sum, bar) => sum + bar.value, 0) / 5
  const volumeReady = data.volume.length >= 6 && data.volume.at(-1)?.time === time
    && baseline > 0 && Number.isFinite(baseline)
  return {
    sma20: currentValue(data.sma20, time),
    sma60: currentValue(data.sma60, time),
    rsi: currentValue(data.rsi, time),
    k: currentValue(data.kd.k, time),
    d: currentValue(data.kd.d, time),
    atr14: currentValue(data.atr14, time),
    macdLine: currentValue(data.macd.line, time),
    macdSignal: currentValue(data.macd.signal, time),
    volumeSma5: currentValue(data.volume_sma5, time),
    volumeSma10: currentValue(data.volume_sma10, time),
    volumeRatio: volumeReady && Number.isFinite(data.latest.volume_ratio)
      ? data.latest.volume_ratio : null,
  }
}

export function describeRsi(value: number | null) {
  if (value == null) return "資料不足或無有效數值，暫不判讀"
  if (value > 70) return "高於 70，近期上漲力道偏強；不代表接著一定下跌"
  if (value < 30) return "低於 30，近期下跌力道偏強；不代表接著一定反彈"
  return "介於 30–70，未達常用超買／超賣門檻，不代表投資風險低"
}

export function describeVolumeRatio(value: number | null) {
  if (value == null) return "需有前 5 根有效均量，且平均量大於零，才能比較"
  const percent = Math.round(Math.abs(value - 1) * 100)
  return percent === 0 ? "本根成交量與前 5 根平均相當"
    : `本根成交量比前 5 根平均${value > 1 ? "多" : "少"} ${percent}%`
}

export function buildIndicatorSignals(data: StockData): IndicatorSignal[] {
  const values = getIndicatorReadings(data)
  const signals: IndicatorSignal[] = []
  const close = data.candles.at(-1)?.close
  if (close != null && values.sma20 != null) {
    signals.push({
      level: close > values.sma20 ? "positive" : close < values.sma20 ? "negative" : "neutral",
      label: `${close > values.sma20 ? "高於" : close < values.sma20 ? "低於" : "等於"} SMA20`,
      desc: `收盤 ${close.toFixed(2)}，20 期均價 ${values.sma20.toFixed(2)}；描述目前位置`,
    })
  }
  if (values.macdLine != null && values.macdSignal != null) {
    const diff = values.macdLine - values.macdSignal
    signals.push({
      level: diff > 0 ? "positive" : diff < 0 ? "negative" : "neutral",
      label: `MACD ${diff > 0 ? "線在上方" : diff < 0 ? "線在下方" : "兩線重合"}`,
      desc: "比較 MACD 線與訊號線的位置，不表示本根剛發生金叉／死叉",
    })
  }
  if (values.rsi != null) {
    signals.push({ level: values.rsi > 70 || values.rsi < 30 ? "warning" : "neutral",
      label: `RSI ${values.rsi.toFixed(1)}`, desc: describeRsi(values.rsi) })
  }
  if (values.volumeRatio != null && (values.volumeRatio >= 1.5 || values.volumeRatio < 0.7)) {
    signals.push({ level: "neutral", label: `量比 ${values.volumeRatio.toFixed(2)} 倍`,
      desc: `${describeVolumeRatio(values.volumeRatio)}；放量本身沒有漲跌方向` })
  }
  for (const pattern of data.patterns) {
    signals.push({ level: pattern.signal === "bullish" ? "positive" : "negative",
      label: `K 線型態：${pattern.name}`, desc: "最近 5 根內的形狀訊號，需配合趨勢與成交量，不保證反轉" })
  }
  return signals
}
