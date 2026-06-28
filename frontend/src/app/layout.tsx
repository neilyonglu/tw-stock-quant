import type { Metadata } from "next"
import { Geist } from "next/font/google"
import { Sidebar } from "@/components/sidebar"
import "./globals.css"

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" })

export const metadata: Metadata = {
  title: "台股分析",
  description: "台灣股市量化分析系統",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW" className={`dark ${geist.variable}`}>
      <body className="flex h-screen bg-zinc-950 text-zinc-100 antialiased">
        <Sidebar />
        <main className="flex-1 overflow-auto">{children}</main>
      </body>
    </html>
  )
}
