import type { IChartApi } from "lightweight-charts"

/**
 * Caps how far a lightweight-charts instance can be zoomed/panned out so the
 * visible range never exceeds the actual data span — the most-zoomed-out
 * state always has real data at both edges, never blank background.
 * Recomputes on container resize (e.g. sidebar collapse, viewport change).
 * Returns a cleanup function to disconnect the resize observer.
 */
export function boundChartZoom(chart: IChartApi, container: HTMLElement, dataLength: number): () => void {
  if (dataLength <= 0) return () => {}

  const timeScale = chart.timeScale()

  function apply() {
    const width = timeScale.width() || container.clientWidth
    if (!width) return
    timeScale.applyOptions({
      fixLeftEdge: true,
      fixRightEdge: true,
      minBarSpacing: width / dataLength,
    })
  }

  apply()
  const observer = new ResizeObserver(apply)
  observer.observe(container)
  return () => observer.disconnect()
}
