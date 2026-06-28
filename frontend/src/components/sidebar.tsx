"use client"
import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronLeft, ChevronRight, BarChart2, LineChart, ListFilter } from "lucide-react"

const navItems = [
  { label: "市場總覽", href: "/market",     match: "/market",    icon: BarChart2 },
  { label: "個股分析", href: "/stock/2330", match: "/stock",     icon: LineChart },
  { label: "每週選股", href: "/screening",  match: "/screening", icon: ListFilter },
]

export function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`shrink-0 flex flex-col h-screen bg-zinc-900 border-r border-zinc-800 transition-all duration-200 ${
        collapsed ? "w-14" : "w-60"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-4 border-b border-zinc-800 min-h-14">
        {!collapsed && (
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold text-white tracking-tight">台股分析</span>
            <a
              href="https://github.com/neilyonglu/tw-stock-quant"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              by neilyonglu
            </a>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors ml-auto"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {navItems.map(({ label, href, match, icon: Icon }) => {
          const active = pathname.startsWith(match)
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-zinc-700 text-white font-medium"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800"
              }`}
            >
              <Icon size={16} className="shrink-0" />
              {!collapsed && <span>{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-zinc-800 text-xs text-zinc-500">
          最後更新：—
        </div>
      )}
    </aside>
  )
}
