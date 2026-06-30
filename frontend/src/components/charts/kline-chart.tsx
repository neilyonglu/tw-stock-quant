"use client"

import { useEffect, useRef } from "react"
import {
  createChart,
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

interface KlineChartProps {
  candles: Candle[]
  volume: VolumeBar[]
  sma20: TimeValue[]
  sma60: TimeValue[]
  rsi: TimeValue[]
  macd: MacdPayload
}

const MAIN_H = 500
const SUB_H = 120

export function KlineChart({ candles, volume, sma20, sma60, rsi, macd }: KlineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

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

    const sma20Series = chart.addSeries(LineSeries, {
      color: "#F59E0B",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, 0)
    sma20Series.setData(sma20)

    const sma60Series = chart.addSeries(LineSeries, {
      color: "#3B82F6",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, 0)
    sma60Series.setData(sma60)

    // Pane 1 — 成交量
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "vol",
    }, 1)
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0 } })
    volumeSeries.setData(volume)

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
  }, [candles, volume, sma20, sma60, rsi, macd])

  return <div ref={containerRef} style={{ height: MAIN_H + SUB_H * 3 }} />
}
