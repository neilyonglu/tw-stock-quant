"use client"

import { useEffect, useRef, useState } from "react"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import type { TickerSearchResult } from "@/lib/types"

// 代碼或名稱關鍵字搜尋，debounce 200ms 打 /api/stock/search（真實資料：twstock 本地代碼表）。
// 不內建導頁邏輯——選到結果或直接按 Enter/搜尋鈕時呼叫 onSelect，由呼叫端決定要切換
// 目前頁面的 activeTicker 還是 router.push 到新頁面。
export function TickerSearch({
  onSelect,
  placeholder = "輸入代碼或名稱，例如 2330 或 台積電",
  id,
}: {
  onSelect: (ticker: string) => void
  placeholder?: string
  id?: string
}) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<TickerSearchResult[]>([])
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const q = query.trim()
    if (!q) {
      setResults([])
      setOpen(false)
      return
    }
    const ctrl = new AbortController()
    const timer = setTimeout(() => {
      fetch(`/api/stock/search?q=${encodeURIComponent(q)}`, { signal: ctrl.signal })
        .then((res) => (res.ok ? (res.json() as Promise<TickerSearchResult[]>) : []))
        .then((data) => {
          setResults(data)
          setOpen(data.length > 0)
          setHighlighted(0)
        })
        .catch(() => {})
    }, 200)
    return () => {
      clearTimeout(timer)
      ctrl.abort()
    }
  }, [query])

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onClickOutside)
    return () => document.removeEventListener("mousedown", onClickOutside)
  }, [])

  function pick(ticker: string) {
    setOpen(false)
    setQuery("")
    onSelect(ticker)
  }

  function submitRaw() {
    const t = query.trim().replace(/\.TW$/i, "")
    if (t) pick(t)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setHighlighted((h) => Math.min(h + 1, results.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setHighlighted((h) => Math.max(h - 1, 0))
    } else if (e.key === "Enter") {
      if (open && results[highlighted]) pick(results[highlighted].ticker)
      else submitRaw()
    } else if (e.key === "Escape") {
      setOpen(false)
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="flex gap-1.5">
        <Input
          id={id}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          className="bg-zinc-900 border-zinc-700 text-sm h-11"
        />
        <Button
          size="sm"
          variant="outline"
          aria-label="搜尋股票代碼"
          className="h-11 w-11 px-0 border-zinc-700 shrink-0"
          onClick={submitRaw}
        >
          <Search size={14} />
        </Button>
      </div>
      {open && (
        <div className="absolute z-20 mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 shadow-lg overflow-hidden">
          {results.map((r, i) => (
            <button
              key={r.ticker}
              onClick={() => pick(r.ticker)}
              onMouseEnter={() => setHighlighted(i)}
              className={`flex w-full items-center gap-2 px-3 py-2.5 min-h-11 text-left text-sm transition-colors ${
                i === highlighted ? "bg-zinc-800 text-white" : "text-zinc-300"
              }`}
            >
              <span className="text-muted-foreground shrink-0">{r.ticker}</span>
              <span className="truncate">{r.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
