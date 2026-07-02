import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Sidebar } from "@/components/sidebar"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: "台股分析",
  description: "台灣股市量化分析系統",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW" className={`dark ${inter.variable}`}>
      <body className="flex h-screen bg-background text-foreground antialiased">
        <Sidebar />
        <main className="flex-1 overflow-auto pb-14 md:pb-0">{children}</main>
      </body>
    </html>
  )
}
