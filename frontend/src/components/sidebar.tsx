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
  // hidden at label text below lg unless the user hasn't collapsed AND viewport is lg+;
  // md (tablet) is always forced to icon-only regardless of the manual toggle
  const labelClass = collapsed ? "hidden" : "hidden lg:inline"
  const asideWidth = collapsed ? "lg:w-14" : "lg:w-60"

  return (
    <>
      {/* Desktop / tablet sidebar */}
      <aside
        className={`hidden md:flex shrink-0 flex-col h-screen w-14 ${asideWidth} bg-zinc-900 border-r border-zinc-800 transition-all duration-200`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-4 border-b border-zinc-800 min-h-14">
          <div className={`${labelClass} flex-col leading-tight`}>
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
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:block p-1 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors ml-auto"
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
                title={label}
                className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm transition-colors ${
                  active
                    ? "bg-zinc-700 text-white font-medium"
                    : "text-zinc-400 hover:text-white hover:bg-zinc-800"
                }`}
              >
                <Icon size={16} className="shrink-0" />
                <span className={labelClass}>{label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className={`${labelClass} px-4 py-3 border-t border-zinc-800 text-xs text-zinc-500`}>
          最後更新：2026/07/02
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed inset-x-0 bottom-0 z-50 h-14 flex items-stretch bg-zinc-900 border-t border-zinc-800">
        {navItems.map(({ label, href, match, icon: Icon }) => {
          const active = pathname.startsWith(match)
          return (
            <Link
              key={href}
              href={href}
              className={`flex-1 flex flex-col items-center justify-center gap-0.5 text-[11px] ${
                active ? "text-white" : "text-zinc-500"
              }`}
            >
              <Icon size={18} />
              <span>{label}</span>
            </Link>
          )
        })}
      </nav>
    </>
  )
}
