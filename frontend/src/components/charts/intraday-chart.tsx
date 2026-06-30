"use client"

import { useEffect, useRef } from "react"
import {
  createChart,
  AreaSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
  type UTCTimestamp,
} from "lightweight-charts"
import type { IntradaySeries } from "@/lib/types"

// 台股慣例：紅漲綠跌（跟美股的 green-up / red-down 相反），跟 kline-chart.tsx 一致
const STOCK_UP = "#EF5350" // 漲：紅
const STOCK_DOWN = "#26A69A" // 跌：綠

const MAIN_H = 300
const SUB_H = 100

export function IntradayChart({ data }: { data: IntradaySeries }) {
  const containerRef = useRef<HTMLDivElement>(null)
  // 指數（如 ^TWII）yfinance 沒有有意義的每分鐘成交量，全部是 0；
  // 這種情況不畫成交量子圖，畫出來也只是一條沒有意義的空白線。
  const hasVolume = data.points.some((p) => p.volume > 0)

  useEffect(() => {
    if (!containerRef.current || !data.points.length) return

    const lastPrice = data.points[data.points.length - 1].price
    const isUp = lastPrice >= data.prev_close
    const lineColor = isUp ? STOCK_UP : STOCK_DOWN
    const chartHeight = hasVolume ? MAIN_H + SUB_H : MAIN_H

    const chart = createChart(containerRef.current, {
      autoSize: true,
      height: chartHeight,
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

    // Pane 0 — 價格（區域圖）+ 均價線 + 平盤參考線
    const priceSeries = chart.addSeries(AreaSeries, {
      lineColor,
      topColor: `${lineColor}33`,
      bottomColor: `${lineColor}00`,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    }, 0)
    priceSeries.setData(data.points.map((p) => ({ time: p.time as UTCTimestamp, value: p.price })))
    priceSeries.createPriceLine({
      price: data.prev_close,
      color: "#71717a",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: "平盤",
    })

    const avgSeries = chart.addSeries(LineSeries, {
      color: "#F59E0B",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    }, 0)
    avgSeries.setData(data.points.map((p) => ({ time: p.time as UTCTimestamp, value: p.avg_price })))

    // Pane 1 — 成交量（指數沒有成交量資料時不畫）
    if (hasVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "vol",
      }, 1)
      volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.1, bottom: 0 } })
      volumeSeries.setData(
        data.points.map((p) => ({
          time: p.time as UTCTimestamp,
          value: p.volume,
          color: p.price >= data.prev_close ? STOCK_UP : STOCK_DOWN,
        }))
      )
    }

    const panes = chart.panes()
    panes[0]?.setHeight(MAIN_H)
    if (hasVolume) panes[1]?.setHeight(SUB_H)

    return () => chart.remove()
  }, [data, hasVolume])

  return <div ref={containerRef} style={{ height: hasVolume ? MAIN_H + SUB_H : MAIN_H }} />
}
