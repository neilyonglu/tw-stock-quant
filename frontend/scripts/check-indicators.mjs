import assert from "node:assert/strict"
import { buildIndicatorSignals, describeRsi, describeVolumeRatio, getIndicatorReadings } from "../src/lib/indicator-summary.ts"

const time = "2026-10-15"
const sample = {
  candles: [{ time, close: 100 }],
  sma20: [{ time, value: 100 }], sma60: [], rsi: [],
  macd: { line: [{ time, value: 0 }], signal: [{ time, value: 0 }], histogram: [] },
  volume_sma5: [], volume_sma10: [], volume: [], patterns: [],
  latest: { rsi: 50, macd_crossover: "dead", volume_ratio: 1 },
}

// Legacy fallback values must not turn missing data into a healthy RSI or bearish crossover.
const signals = buildIndicatorSignals(sample)
assert.equal(getIndicatorReadings(sample).rsi, null)
assert.equal(getIndicatorReadings(sample).volumeRatio, null)
assert(!signals.some((signal) => signal.label.startsWith("RSI")))
assert(signals.some((signal) => signal.label === "MACD 兩線重合" && signal.level === "neutral"))
assert(signals.some((signal) => signal.label === "等於 SMA20" && signal.level === "neutral"))

const valid = { ...sample, rsi: [{ time, value: 75 }],
  volume: Array.from({ length: 6 }, (_, i) => ({ time: i === 5 ? time : `bar-${i}`, value: 100 })),
  macd: { ...sample.macd, line: [{ time, value: 2 }], signal: [{ time, value: 1 }] },
  latest: { ...sample.latest, volume_ratio: 1.5 } }
assert.equal(getIndicatorReadings(valid).volumeRatio, 1.5)
assert.equal(getIndicatorReadings(valid).rsi, 75)
assert(buildIndicatorSignals(valid).some((signal) => signal.label === "MACD 線在上方"))
assert(!buildIndicatorSignals(valid).some((signal) => /金叉|死叉|突破|跌破/.test(signal.label)))
assert(buildIndicatorSignals(valid).some((signal) => signal.label === "量比 1.50 倍" && signal.level === "neutral"))
assert.match(describeVolumeRatio(1.5), /多 50%/)
assert.match(describeVolumeRatio(0.5), /少 50%/)
assert.match(describeRsi(50), /不代表投資風險低/)

assert.equal(getIndicatorReadings({ ...valid, rsi: [{ time: "2026-10-14", value: 80 }] }).rsi, null)
assert.equal(getIndicatorReadings({ ...valid, rsi: [{ time, value: NaN }] }).rsi, null)
assert.equal(getIndicatorReadings({ ...valid, volume: valid.volume.map((bar) => ({ ...bar, value: 0 })) }).volumeRatio, null)
assert.equal(getIndicatorReadings({ ...valid, latest: { ...valid.latest, volume_ratio: Infinity } }).volumeRatio, null)
console.log("PASS: missing/stale data, neutral states, MACD position and volume explanations")
