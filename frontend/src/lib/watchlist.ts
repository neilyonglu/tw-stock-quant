// 自選股清單，存在使用者這台電腦的瀏覽器（localStorage），換裝置或清瀏覽器資料會消失。
// 之後若要換成後端資料庫同步，只要換掉這支檔案內部的實作，呼叫端（元件）不用改。

import { useSyncExternalStore } from "react"

const STORAGE_KEY = "stock-analysis:watchlist"
const EMPTY: string[] = []

// useSyncExternalStore 要求 snapshot 沒變就回傳同一個陣列參考，否則每次 render 都被當成「變了」會無限迴圈。
// 用 cachedRaw 記住上次讀到的原始字串，raw 沒變就直接回傳快取的陣列。
let cachedRaw: string | null = null
let cachedParsed: string[] = EMPTY

function readRaw(): string[] {
  if (typeof window === "undefined") return EMPTY
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (raw === cachedRaw) return cachedParsed
  cachedRaw = raw
  try {
    if (!raw) {
      cachedParsed = EMPTY
    } else {
      const parsed = JSON.parse(raw)
      cachedParsed = Array.isArray(parsed) ? parsed.filter((t) => typeof t === "string") : EMPTY
    }
  } catch {
    cachedParsed = EMPTY
  }
  return cachedParsed
}

function writeRaw(tickers: string[]) {
  if (typeof window === "undefined") return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(tickers))
  window.dispatchEvent(new Event("watchlist-changed"))
}

export function removeFromWatchlist(ticker: string) {
  writeRaw(readRaw().filter((t) => t !== ticker))
}

export function toggleWatchlist(ticker: string) {
  const current = readRaw()
  if (current.includes(ticker)) {
    writeRaw(current.filter((t) => t !== ticker))
  } else {
    writeRaw([...current, ticker])
  }
}

// 讓元件即時反映自選股變化（同分頁內加入/移除、跨分頁 storage 事件都會觸發重新渲染）
function subscribe(callback: () => void) {
  window.addEventListener("watchlist-changed", callback)
  window.addEventListener("storage", callback)
  return () => {
    window.removeEventListener("watchlist-changed", callback)
    window.removeEventListener("storage", callback)
  }
}

function getServerSnapshot(): string[] {
  return EMPTY
}

export function useWatchlist(): string[] {
  return useSyncExternalStore(subscribe, readRaw, getServerSnapshot)
}
