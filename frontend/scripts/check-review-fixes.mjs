import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { createRequire } from "node:module"
import vm from "node:vm"
import ts from "typescript"

const require = createRequire(import.meta.url)
function harness(file, overrides = {}) {
  const slots = [], pending = []
  let index = 0
  const react = {
    useState(initial) {
      const key = index++
      if (!(key in slots)) slots[key] = typeof initial === "function" ? initial() : initial
      return [slots[key], (next) => { slots[key] = typeof next === "function" ? next(slots[key]) : next }]
    },
    useRef(initial) { return react.useState(() => ({ current: initial }))[0] },
    useId() { return react.useState("search-id")[0] },
    useMemo(callback, deps) {
      const key = index++
      if (!slots[key] || deps.some((dep, i) => dep !== slots[key].deps[i])) slots[key] = { deps, value: callback() }
      return slots[key].value
    },
    useCallback(callback, deps) { return react.useMemo(() => callback, deps) },
    useEffect(callback, deps) {
      const key = index++
      if (!slots[key] || deps.some((dep, i) => dep !== slots[key].deps[i])) {
        slots[key]?.cleanup?.()
        slots[key] = { deps }
        pending.push(() => { slots[key].cleanup = callback() })
      }
    },
    useSyncExternalStore(_subscribe, snapshot) { return snapshot() },
  }
  const exports = {}
  const code = ts.transpileModule(readFileSync(new URL(`../src/${file}`, import.meta.url), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
  }).outputText
  const context = {
    exports, console, AbortController, Event, Date,
    fetch: (...args) => overrides.fetch(...args),
    window: overrides.window,
    document: { addEventListener() {}, removeEventListener() {}, hidden: false },
    setInterval: () => 1, clearInterval() {}, setTimeout, clearTimeout,
    require(name) {
      if (name === "react") return react
      if (name === "react/jsx-runtime") return require(name)
      if (name in overrides.modules) return overrides.modules[name]
      if (name === "@/lib/utils") return { cn: () => "", formatDateTime: String, formatTimeShort: String }
      return new Proxy({}, { get: (_obj, key) => key })
    },
  }
  overrides.modules ??= {}
  vm.runInNewContext(code, context, { filename: file })
  return {
    exports,
    render(name, props = {}) {
      index = 0
      const tree = exports[name](props)
      pending.splice(0).forEach((effect) => effect())
      return tree
    },
    slots,
  }
}
function nodes(tree) {
  if (!tree || typeof tree !== "object") return []
  if (Array.isArray(tree)) return tree.flatMap(nodes)
  return [tree, ...nodes(tree.props?.children)]
}
const settle = () => new Promise((resolve) => setImmediate(resolve))

for (const failure of [() => Promise.resolve({ ok: false }), () => Promise.reject(new Error("offline"))]) {
  let requests = 0
  const h = harness("components/screening-view.tsx", { fetch: () => ++requests === 1 ? failure() : Promise.resolve({ ok: true, json: async () => ({ results: [], allocation: [], market_environment: "多頭", updated_at: "2026-10-21" }) }) })
  h.render("ScreeningView")
  await settle()
  let tree = h.render("ScreeningView")
  assert(nodes(tree).some((node) => node.props?.role === "alert"), "screening failure is visible")
  await nodes(tree).find((node) => node.props?.onClick && node.props?.disabled === false).props.onClick()
  tree = h.render("ScreeningView")
  assert(!nodes(tree).some((node) => node.props?.role === "alert"), "screening retry recovers")
}

let raw = '["2330"]', failRead = false, failWrite = false
const store = harness("lib/watchlist.ts", { window: {
  localStorage: {
    getItem() { if (failRead) throw new Error("SecurityError"); return raw },
    setItem(_key, value) { if (failWrite) throw new Error("QuotaExceededError"); raw = value },
  }, dispatchEvent() {},
} }).exports
assert.equal(store.useWatchlist().join(), "2330")
failRead = true
assert.equal(store.toggleWatchlist("2454"), false, "unreadable storage cannot overwrite existing list")
assert.equal(raw, '["2330"]')
failRead = false
failWrite = true
assert.equal(store.toggleWatchlist("2454"), false, "failed save is reported")
assert.equal(store.useWatchlist().join(), "2330", "failed save does not alter snapshot")
failWrite = false
assert.equal(store.toggleWatchlist("2454"), true)
assert.equal(store.useWatchlist().join(), "2330,2454")
assert.equal(store.removeFromWatchlist("2330"), true)
assert.equal(store.useWatchlist().join(), "2454")
raw = "invalid-json"
assert.equal(store.useWatchlist().length, 0)
assert.equal(store.toggleWatchlist("2330"), true, "readable corrupt storage can recover")
assert.equal(store.useWatchlist().join(), "2330")

for (const [file, name, payload] of [
  ["components/stock/intraday-tab.tsx", "IntradayTab", { points: [{ time: 1, price: 2 }], prev_close: 1 }],
  ["components/stock/order-book.tsx", "OrderBook", { asks: [{ price: 2, volume: 1 }], bids: [] }],
  ["components/market/intraday-section.tsx", "MarketIntradaySection", { points: [{ time: 1, price: 2 }], prev_close: 1 }],
]) {
  let requests = 0
  const h = harness(file, { fetch: async () => { requests++; return { ok: true, json: async () => payload } } })
  h.render(name, { ticker: "2330", refreshKey: 0 })
  await settle()
  h.render(name, { ticker: "2330", refreshKey: 0 })
  assert.equal(requests, 1)
  h.render(name, { ticker: "2330", refreshKey: 1 })
  await settle()
  assert.equal(requests, 2, `${name} follows parent refresh`)
}

let selectedTicker
const search = harness("components/ticker-search.tsx", { fetch: async () => ({ ok: true, json: async () => [{ ticker: "2330", name: "TSMC" }, { ticker: "2454", name: "MediaTek" }] }) })
const searchProps = { onSelect(ticker) { selectedTicker = ticker } }
let input = nodes(search.render("TickerSearch", searchProps)).find((node) => node.props?.role === "combobox")
assert(input.props["aria-label"])
assert.equal(input.props["aria-expanded"], false)
input.props.onChange({ target: { value: "23" } })
search.render("TickerSearch", searchProps)
await new Promise((resolve) => setTimeout(resolve, 220))
input = nodes(search.render("TickerSearch", searchProps)).find((node) => node.props?.role === "combobox")
assert.equal(input.props["aria-expanded"], true)
input.props.onKeyDown({ key: "ArrowDown", preventDefault() {} })
const searchTree = search.render("TickerSearch", searchProps)
input = nodes(searchTree).find((node) => node.props?.role === "combobox")
const activeOption = nodes(searchTree).find((node) => node.props?.id === input.props["aria-activedescendant"])
assert(activeOption.props["aria-selected"])
input.props.onKeyDown({ key: "Enter" })
assert.equal(selectedTicker, "2454", "keyboard selection agrees with announced active option")

const charts = []
function createChart() {
  const scale = { range: null, applyOptions() {}, width: () => 100,
    getVisibleLogicalRange() { return this.range }, setVisibleLogicalRange(range) { this.range = range } }
  const chart = { scale, timeScale: () => scale, panes: () => [], remove() {},
    addSeries: () => ({ setData() {}, createPriceLine() {}, priceScale: () => ({ applyOptions() {} }) }) }
  charts.push(chart)
  return chart
}
const chartModule = { createChart, createSeriesMarkers() {}, ColorType: { Solid: 0 }, CrosshairMode: { Magnet: 0 }, LineStyle: { Dashed: 0 } }
const chart = harness("components/charts/kline-chart.tsx", { modules: {
  "lightweight-charts": chartModule, "@/lib/chart-zoom-bound": { boundChartZoom: () => () => {} },
} })
const props = { candles: [{ time: "2026-10-21", high: 2, low: 1 }], volume: [], sma20: [], sma60: [], volumeSma5: [], volumeSma10: [], rsi: [], macd: { line: [], signal: [], histogram: [] }, kd: { k: [], d: [] }, atr14: [] }
chart.render("KlineChart", props)
chart.slots[0].current = {}
chart.render("KlineChart", { ...props, candles: [...props.candles] })
charts[0].scale.range = { from: 12, to: 40 }
chart.render("KlineChart", { ...props, candles: [...props.candles] })
assert.deepEqual(charts[1].scale.range, { from: 12, to: 40 }, "background refresh preserves visible chart range")
console.log("PASS: screening failure/retry, storage read/write failures, quote refresh, search label, chart range")

