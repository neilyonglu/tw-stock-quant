import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { ThemeProvider } from "@/components/theme-provider"
import { Sidebar } from "@/components/sidebar"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: "台股分析",
  description: "台灣股市量化分析系統",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // suppressHydrationWarning prevents mismatch when next-themes sets class on hydration
    <html lang="zh-TW" className={inter.variable} suppressHydrationWarning>
      <body className="flex h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <Sidebar />
          <main className="flex-1 overflow-auto">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  )
}
