"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { label: "市場總覽", href: "/market",     match: "/market" },
  { label: "個股分析", href: "/stock/2330", match: "/stock" },
  { label: "每週選股", href: "/screening",  match: "/screening" },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-52 shrink-0 flex flex-col h-screen bg-zinc-900 border-r border-zinc-800">
      <div className="px-4 py-5 border-b border-zinc-800">
        <span className="text-base font-semibold text-white tracking-tight">台股分析</span>
      </div>

      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.match)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-zinc-700 text-white font-medium"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800"
              }`}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-3 border-t border-zinc-800 text-xs text-zinc-500">
        最後更新：—
      </div>
    </aside>
  )
}
