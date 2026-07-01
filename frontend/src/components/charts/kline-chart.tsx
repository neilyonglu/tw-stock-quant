"use client"

import { useEffect, useMemo, useRef } from "react"
import {
  createChart,
  createSeriesMarkers,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
} from "lightweight-charts"
import type { Candle, VolumeBar, TimeValue, MacdPayload } from "@/lib/types"

export type { Candle, VolumeBar, TimeValue, MacdPayload }

// 台股慣例：紅漲綠跌（跟美股的 green-up / red-down 相反）
const STOCK_UP = "#EF5350" // 漲：紅
const STOCK_DOWN = "#26A69A" // 跌：綠

// 短週期均線＝amber、長週期均線＝blue，主圖 SMA20/60 跟成交量 MA5/10 共用同一套配色慣例
const MA_SHORT = "#F59E0B"
const MA_LONG = "#3B82F6"

interface KlineChartProps {
  candles: Candle[]
  volume: VolumeBar[]
  sma20: TimeValue[]
  sma60: TimeValue[]
  volumeSma5: TimeValue[]
  volumeSma10: TimeValue[]
  rsi: TimeValue[]
  macd: MacdPayload
}

const MAIN_H = 500
const SUB_H = 120

// 趨勢箭頭：比較均線最後兩個點的方向，跟電視看盤軟體「均線數值旁加箭頭」的做法一樣
function trendArrow(series: TimeValue[]): string {
  if (series.length < 2) return ""
  const last = series[series.length - 1].value
  const prev = series[series.length - 2].value
  return last >= prev ? "↑" : "↓"
}

export function KlineChart({ candles, volume, sma20, sma60, volumeSma5, volumeSma10, rsi, macd }: KlineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  const legend = useMemo(() => {
    const sma20Last = sma20[sma20.length - 1]?.value
    const sma60Last = sma60[sma60.length - 1]?.value
    return {
      sma20: sma20Last != null ? `SMA20 ${sma20Last.toFixed(2)}${trendArrow(sma20)}` : null,
      sma60: sma60Last != null ? `SMA60 ${sma60Last.toFixed(2)}${trendArrow(sma60)}` : null,
    }
  }, [sma20, sma60])

  useEffect(() => {
    if (!containerRef.current || !candles.length) return

    const chart = createChart(containerRef.current, {
      autoSize: true,
      height: MAIN_H + SUB_H * 3,
      layout: {
        background: { type: ColorType.Solid, color: "#09090B" },
        textColor: "#a1a1aa",
        fontFamily: "Inter, sans-serif",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#27272a" },
        horzLines: { color: "#27272a" },
      },
      crosshair: { mode: CrosshairMode.Magnet },
      timeScale: {
        borderColor: "#3f3f46",
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: { borderColor: "#3f3f46" },
    })

    // Pane 0 — K 線 + SMA20 + SMA60
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: STOCK_UP,
      downColor: STOCK_DOWN,
      borderUpColor: STOCK_UP,
      borderDownColor: STOCK_DOWN,
      wickUpColor: STOCK_UP,
      wickDownColor: STOCK_DOWN,
    }, 0)
    candleSeries.setData(candles)

    // 區間最高/最低價直接標在圖上（電視看盤軟體常見做法，不用自己在圖上找高低點）
    if (candles.length > 0) {
      const highest = candles.reduce((a, b) => (b.high > a.high ? b : a))
      const lowest = candles.reduce((a, b) => (b.low < a.low ? b : a))
      createSeriesMarkers(candleSeries, [
        { time: highest.time, position: "aboveBar", color: STOCK_UP, shape: "arrowDown", text: highest.high.toFixed(2) },
        { time: lowest.time, position: "belowBar", color: STOCK_DOWN, shape: "arrowUp", text: lowest.low.toFixed(2) },
      ])
    }

    const sma20Series = chart.addSeries(LineSeries, {
      color: MA_SHORT,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, 0)
    sma20Series.setData(sma20)

    const sma60Series = chart.addSeries(LineSeries, {
      color: MA_LONG,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, 0)
    sma60Series.setData(sma60)

    // Pane 1 — 成交量 + 均量線（MA5/MA10，跟主圖 SMA20/60 同一套短/長週期配色）
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "vol",
    }, 1)
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0 } })
    volumeSeries.setData(volume)

    const volumeSma5Series = chart.addSeries(LineSeries, {
      color: MA_SHORT,
      lineWidth: 1,
      priceScaleId: "vol",
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, 1)
    volumeSma5Series.setData(volumeSma5)

    const volumeSma10Series = chart.addSeries(LineSeries, {
      color: MA_LONG,
      lineWidth: 1,
      priceScaleId: "vol",
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, 1)
    volumeSma10Series.setData(volumeSma10)

    // Pane 2 — RSI(14)
    const rsiSeries = chart.addSeries(LineSeries, {
      color: "#8B5CF6",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
    }, 2)
    rsiSeries.setData(rsi)
    rsiSeries.createPriceLine({
      price: 70,
      color: "#EF5350",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: false,
      title: "超買",
    })
    rsiSeries.createPriceLine({
      price: 30,
      color: "#26A69A",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: false,
      title: "超賣",
    })

    // Pane 3 — MACD
    const macdLineSeries = chart.addSeries(LineSeries, {
      color: "#3B82F6",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    }, 3)
    macdLineSeries.setData(macd.line)

    const macdSignalSeries = chart.addSeries(LineSeries, {
      color: "#F59E0B",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    }, 3)
    macdSignalSeries.setData(macd.signal)

    const histSeries = chart.addSeries(HistogramSeries, {
      priceLineVisible: false,
      lastValueVisible: false,
    }, 3)
    histSeries.setData(
      macd.histogram.map((d) => ({
        ...d,
        color: d.value >= 0 ? `${STOCK_UP}80` : `${STOCK_DOWN}80`,
      }))
    )

    // 設定各 pane 高度
    const panes = chart.panes()
    panes[0]?.setHeight(MAIN_H)
    panes[1]?.setHeight(SUB_H)
    panes[2]?.setHeight(SUB_H)
    panes[3]?.setHeight(SUB_H)

    return () => chart.remove()
  }, [candles, volume, sma20, sma60, volumeSma5, volumeSma10, rsi, macd])

  return (
    <div className="relative">
      {(legend.sma20 || legend.sma60) && (
        <div className="absolute top-1.5 left-3 z-10 flex gap-3 text-xs tabular-nums pointer-events-none">
          {legend.sma20 && <span style={{ color: MA_SHORT }}>{legend.sma20}</span>}
          {legend.sma60 && <span style={{ color: MA_LONG }}>{legend.sma60}</span>}
        </div>
      )}
      <div ref={containerRef} style={{ height: MAIN_H + SUB_H * 3 }} />
    </div>
  )
}
