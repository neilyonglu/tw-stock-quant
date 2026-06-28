# UI 計畫書 — 台股分析系統 Dashboard

> 根據 todo.md、plan.md，結合 ui-ux-pro-max + ui-styling skill 查詢結果撰寫。

---

## 設計方向總結

| 面向 | 決策 | 來源 |
|------|------|------|
| 風格 | Modern Dark — 深色主題為主，類 Linear 排版 | todo.md + design system |
| 參考產品 | Robinhood（結論優先）+ Linear（排版層次） | todo.md |
| 目標受眾 | 一般大眾，非專業交易員；指標要有白話說明 | CLAUDE.md |
| 主框架 | Next.js 15（App Router）+ Tailwind + shadcn/ui | todo.md |
| 圖表 | TradingView lightweight-charts（K 線）+ shadcn Chart（圓餅） | todo.md |
| shadcn 風格 | `base-nova`（Tailwind v4 預設，oklch 色彩，sharp corners 透過 `--radius: 0.25rem` 達成）| ui-styling |

---

## 前端檔案結構

```
frontend/
├── package.json
├── next.config.ts
├── tailwind.config.ts              # darkMode: ['class'] + 自訂 token
├── components.json                 # shadcn: style="new-york", baseColor="zinc"
│
├── src/
│   ├── app/
│   │   ├── globals.css             # CSS variables（HSL 格式）+ 全域樣式
│   │   ├── layout.tsx              # RootLayout：ThemeProvider + Sidebar + main
│   │   ├── page.tsx                # redirect → /market
│   │   ├── market/
│   │   │   └── page.tsx            # 頁面一：市場總覽
│   │   ├── stock/
│   │   │   └── [ticker]/
│   │   │       └── page.tsx        # 頁面二：個股 K 線分析
│   │   ├── screening/
│   │   │   └── page.tsx            # 頁面三：每週選股結果
│   │   └── api/
│   │       └── stock/
│   │           └── [ticker]/
│   │               └── route.ts    # Route Handler：呼叫 Python 取 yfinance 資料
│   │
│   ├── components/
│   │   ├── ui/                     # shadcn/ui 自動產生（勿手動修改）
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── alert.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── toggle-group.tsx
│   │   │   ├── table.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── toast.tsx
│   │   │   └── chart.tsx           # shadcn Chart（Recharts wrapper）
│   │   │
│   │   ├── sidebar.tsx             # 側欄導航
│   │   ├── theme-provider.tsx      # next-themes ThemeProvider
│   │   ├── stat-card.tsx           # 指數 / 指標卡（通用模板）
│   │   ├── signal-badge.tsx        # ✅ ⚠️ ❌ 技術訊號標示
│   │   ├── market-banner.tsx       # 環境結論橫幅（多頭/盤整/空頭）
│   │   └── charts/
│   │       └── kline-chart.tsx     # TradingView lightweight-charts 封裝
│   │
│   └── lib/
│       ├── utils.ts                # cn() shadcn 工具函數
│       └── mock-data.ts            # 建皮期間 mock 資料
```

---

## 設計 Token

### CSS 變數（`globals.css`）

shadcn 使用 **HSL 格式**（不含 `hsl()` wrapper），方便 Tailwind 做 opacity 組合：

> **注意**：ui_plan.md 撰寫時預設舊版 shadcn（HSL 格式）。實際安裝為 shadcn 4.x + Tailwind v4，使用 `oklch` 色彩格式與 `base-nova` style。以下 token 值為設計意圖參考，實際實作已轉換為 oklch 並寫入 `globals.css`。

```css
@layer base {
  :root {
    /* shadcn 標準 token（zinc 基色）*/
    --background:   240 10% 4%;      /* #09090B 近黑，避免純黑 */
    --foreground:   0 0% 98%;        /* slate-50 */
    --card:         240 10% 7%;      /* zinc-900 */
    --card-foreground: 0 0% 98%;
    --muted:        240 4% 16%;      /* zinc-800 */
    --muted-foreground: 240 5% 65%; /* zinc-400 */
    --border:       240 4% 22%;      /* zinc-700 */
    --input:        240 4% 22%;
    --ring:         142 76% 36%;     /* emerald-600，focus ring */
    --radius:       0.25rem;         /* Linear-style 極小圓角 */

    /* 語意色（股票專用，疊加在 shadcn 上）*/
    --stock-up:     174 52% 39%;     /* #26A69A TradingView teal */
    --stock-down:   4 79% 62%;       /* #EF5350 TradingView red */
    --stock-warn:   38 92% 50%;      /* #F59E0B amber */
    --stock-info:   217 91% 60%;     /* #3B82F6 blue */

    /* primary = emerald（CTA / active nav）*/
    --primary:      142 76% 36%;     /* #059669 */
    --primary-foreground: 0 0% 98%;
    --accent:       240 4% 16%;
    --accent-foreground: 0 0% 98%;
    --destructive:  4 79% 62%;
    --destructive-foreground: 0 0% 98%;
  }
  /* 本專案固定深色，不提供 :root（光亮）variant */
}

/* 數字一律用等寬字形，防止表格跳動 */
@layer base {
  .tabular { font-variant-numeric: tabular-nums; }
  td, th { font-variant-numeric: tabular-nums; }
}
```

### 字體

```
字族：Inter（Next.js next/font/google 最佳化載入）
大小尺度：12 / 14 / 16 / 18 / 24 / 32 px
行高：body 1.5–1.6；標題 1.2
```

### 間距

4dp 倍數系統：4 / 8 / 12 / 16 / 24 / 32 / 48 px

---

## shadcn 初始化指令

```bash
cd frontend

# 初始化（選 New York style、zinc 基色、CSS variables: yes）
npx shadcn@latest init

# 安裝所有需要的元件
npx shadcn@latest add button card badge alert input select toggle-group \
  table skeleton progress sonner chart
```

> **為什麼選 New York**：sharp corners（`--radius: 0.25rem`）、高對比，視覺上更接近 Linear + TradingView 的精準感。Default style 較圓潤，更適合消費者 app。

---

## 深色主題實作（next-themes）

```tsx
// components/theme-provider.tsx
"use client"
import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="dark" disableTransitionOnChange>
      {children}
    </NextThemesProvider>
  )
}
```

```tsx
// app/layout.tsx
<html lang="zh-TW" suppressHydrationWarning>  {/* suppressHydrationWarning 必要 */}
  <body>
    <ThemeProvider>...</ThemeProvider>
  </body>
</html>
```

> 用 next-themes 而不是 hardcode `className="dark"`，避免 SSR/CSR hydration mismatch。  
> `defaultTheme="dark"` 確保首次載入就是深色，不閃白。

---

## Layout 架構

```
┌──────────────────────────────────────────────────────────────┐
│  Sidebar (固定寬 240px，桌面；手機收合為 icon bar)            │
│  ┌────────────────┐  ┌─────────────────────────────────────┐ │
│  │ 台股分析         │  │  <main>  每頁獨立內容               │ │
│  │                │  │                                     │ │
│  │ ● 市場總覽      │  │                                     │ │
│  │ ● 個股分析      │  │                                     │ │
│  │ ● 每週選股      │  │                                     │ │
│  │                │  │                                     │ │
│  │ ──────────────  │  │                                     │ │
│  │ 最後更新：13:30  │  │                                     │ │
│  └────────────────┘  └─────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**技術實作：**

```tsx
// layout.tsx 骨架
<div className="flex min-h-dvh">           {/* min-h-dvh 避免手機 viewport 問題 */}
  <Sidebar className="w-60 shrink-0" />   {/* hidden md:flex */}
  <main className="flex-1 overflow-auto">
    {children}
  </main>
</div>
```

- 側欄背景：`bg-card border-r border-border`
- active nav 項：`bg-accent text-primary font-medium`
- 手機（< 768px）：sidebar 改成底部 fixed bar，最多 4 項（市場/個股/選股/－）
- 不用 drawer pattern（navigation-consistency 原則：位置不隨頁面改變）

---

## 頁面一：市場總覽 `/market`

> 核心問題：「現在適合操作嗎？」

### 佈局

```
┌─────────────────────────────────────────────┐
│  台股市場總覽  2026-07-04  13:30    [重新整理] │
├──────────┬─────────┬──────────┬─────────────┤
│  加權指數  │ 景氣燈號 │ USD/TWD  │  美債 10Y   │
│ 22,450   │  綠燈    │  31.8   │   4.35%     │
│  +1.2%   │ （說明）  │  -0.3   │   ±0.02    │
└──────────┴─────────┴──────────┴─────────────┘

┌─────────────────────────────────────────────┐
│  三大法人今日買賣超（3 欄卡片）               │
│  外資 +85億    投信 +12億    自營 -3億        │
│  「外國大資金今天在買，是好訊號」             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  市場廣度（5 個數字橫排）                     │
│  漲：650  跌：280  平：120  漲停：23  跌停：2  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  市場環境：多頭   建議操作強度：積極           │
│  （全寬橫幅，顏色依多頭/盤整/空頭切換）       │
└─────────────────────────────────────────────┘
```

### 元件對照

| 區塊 | shadcn 元件 | 備註 |
|------|------------|------|
| 四個指數卡 | `StatCard`（自訂，內用 `Card`）| 漲跌用 `text-[hsl(var(--stock-up))]` |
| 三大法人 | `Card` × 3，grid-cols-3 | 底部一行白話說明 |
| 市場廣度 | 自訂 5 格 flex | 數字 text-2xl，說明 text-xs text-muted-foreground |
| 環境結論橫幅 | 自訂 `MarketBanner` | className 依多頭/盤整/空頭切 border-l-4 顏色 |
| 重新整理 | `Button variant="outline" size="sm"` | 非同步時 disabled + Lucide `RotateCw` 轉圈 |
| 載入中 | `Skeleton` | StatCard 骨架佔位 |

### 設計重點

- 每個指標都加一行白話說明（目標受眾是一般大眾）
- 漲跌用 `hsl(var(--stock-up/down))`，不寫死 hex
- 景氣燈號用純文字 + 色點（避免 emoji 作圖示，符合 no-emoji-icons 原則）
- 結論橫幅是頁面唯一 primary 焦點

---

## 頁面二：個股 K 線分析 `/stock/[ticker]`

> 核心問題：「這支股票現在可以進場嗎？」

### 佈局

```
┌───────────────┬─────────────────────────────────────────┐
│  左側欄（240px）│  主圖區                                 │
│               │                                         │
│  股票代碼輸入   │  台積電 (2330)  930  +1.5%  +13.95      │
│  [2330  ]     │  ─────────────────────────────────────  │
│  [查詢]        │  [K線主圖 500px]  SMA20 橘 / SMA60 藍   │
│               │  ─────────────────────────────────────  │
│  時間區間       │  [成交量子圖 120px]                      │
│  1M 3M 6M 1Y  │  [RSI 子圖 120px]                        │
│               │  [MACD 子圖 120px]                       │
│  ─────────── │  ─────────────────────────────────────  │
│  技術訊號       │  [4欄 StatCard：現價/RSI/MACD/量比]     │
│  ✅ 站上 MA20  │                                         │
│  ✅ MACD 金叉  │                                         │
│  ✅ RSI 55     │                                         │
│  ⚠️ 布林上軌   │                                         │
└───────────────┴─────────────────────────────────────────┘
```

### 圖表規格（`kline-chart.tsx`）

```
TradingView lightweight-charts 五層：

主圖（createChart）：
  candlestickSeries：upColor #26A69A / downColor #EF5350 / wickUpColor / wickDownColor 同
  lineSeries SMA20：color #F59E0B（amber）
  lineSeries SMA60：color #3B82F6（blue）
  高度：500px | background：hsl(var(--background))

子圖共用 timeScale，獨立 chart 實例（syncCrosshair）：
  子圖 1 成交量：histogramSeries，放量 > 1.5x 均量用 stock-up 亮色
  子圖 2 RSI：lineSeries + createPriceLine 70/30（dashed）
  子圖 3 MACD：lineSeries MACD + Signal + histogramSeries Histogram
  子圖高度：120px

載入中：顯示 Skeleton 佔位（高度對應各子圖）
```

### 速查 Card（4 欄）

| Card | 顯示 | 顏色邏輯 |
|------|------|---------|
| 現價 / 漲跌幅 | 930 / +1.5% | `text-[hsl(var(--stock-up/down))]` |
| RSI | 55 + Badge「健康」 | <30 紅 / 30–70 綠 / >70 黃 |
| MACD | 金叉 / 死叉 | Badge `default` / `destructive` |
| 量比 | 1.8x 均量 | ≥1.5x 用 stock-up 強調 |

每張 Card 底部加一行白話說明（`text-xs text-muted-foreground`）。

### 元件對照

| 區塊 | 元件 |
|------|------|
| 代碼輸入 | `Input` + `Button` |
| 時間區間 | `ToggleGroup` + `ToggleGroupItem` |
| 圖表容器 | `kline-chart.tsx`（React ref）|
| 圖表載入 | `Skeleton` × 4 層 |
| 速查卡 | `StatCard` × 4，`grid-cols-2 md:grid-cols-4` |
| 技術訊號清單 | `SignalBadge`（Lucide 圖示，非 emoji）|

---

## 頁面三：每週選股結果 `/screening`

> 核心問題：「本週該買什麼？」

### 佈局

```
┌─────────────────────────────────────────────────────────┐
│  最後更新：2026-07-04 14:00      市場環境：多頭            │
├──────────────────────────────┬──────────────────────────┤
│  選股表格（左 65%）           │  投組配置（右 35%）        │
│                              │                          │
│  [DataTable 可排序]           │  [shadcn Chart PieChart] │
│  排名/股票/評分/理由/進場/停損/% │  台積電 20% / 聯發科 15%  │
│                              │  ...  現金 X%            │
│  點擊代碼 → /stock/[ticker]   │                          │
├──────────────────────────────┴──────────────────────────┤
│  [下載 CSV]                                              │
└─────────────────────────────────────────────────────────┘
```

### 表格欄位

| 欄 | 說明 | 可排序 |
|----|------|--------|
| # | 排名 | ✓ |
| 股票 | 代碼 + 名稱，可點擊跳轉 | ✓ |
| 評分 | 0–100，Badge 顏色分層 | ✓ |
| 推薦理由 | 三層摘要（法人/技術/基本面，三行）| ✗ |
| 進場區間 | 低–高價格 | ✗ |
| 停損 | 價格 + 跌幅 % | ✗ |
| 配置 % | 數字 + `Progress` bar | ✓ |

### 元件對照

| 區塊 | 元件 |
|------|------|
| 資料表 | shadcn `DataTable`（TanStack Table）|
| 排序 | `ColumnDef` + `getSortedRowModel` |
| 圓餅圖 | `shadcn Chart`（`npx shadcn@latest add chart`）|
| 評分徽章 | `Badge`（80+ default / 60–79 secondary / <60 outline）|
| 配置比例 | `Progress` mini bar |
| 下載 CSV | `Button` + 原生 Blob |

### 設計重點

- 手機版（< 768px）：圓餅圖移到表格下方，表格橫向捲動（`overflow-x-auto`）
- 「推薦理由」欄三行分層，`text-xs text-muted-foreground` 做弱化
- 評分欄用 `tabular-nums` 對齊

---

## 共用元件清單

| 元件 | 路徑 | 說明 |
|------|------|------|
| Sidebar | `components/sidebar.tsx` | 導航 + 最後更新時間 |
| ThemeProvider | `components/theme-provider.tsx` | next-themes wrapper |
| KlineChart | `components/charts/kline-chart.tsx` | lightweight-charts 封裝 |
| StatCard | `components/stat-card.tsx` | 指數 / 指標通用卡 |
| SignalBadge | `components/signal-badge.tsx` | 技術訊號標示（Lucide icon，非 emoji）|
| MarketBanner | `components/market-banner.tsx` | 環境結論橫幅 |

---

## 響應式斷點

| 寬度 | 行為 |
|------|------|
| < 768px（手機） | Sidebar 隱藏改底部 fixed nav（4 項 icon + label，44px 高）|
| 768–1023px（平板） | Sidebar 縮成 56px icon bar |
| ≥ 1024px（桌面） | 完整 240px Sidebar |

---

## 實作順序（對應 todo.md Step）

| Step | 內容 | 依賴 |
|------|------|------|
| 0 | `frontend/` init、shadcn init（New York / zinc）、安裝套件 | 無 |
| 1 | Layout + ThemeProvider + Sidebar + 路由框架 | Step 0 |
| 2 | 頁面二 K 線圖（`kline-chart.tsx` + Route Handler mock）| Step 1 |
| 3 | 頁面一 市場總覽（全 mock 資料）| Step 1 |
| 4 | 頁面三 選股表 + 圓餅圖（全 mock 資料）| Step 1 |
| 5 | 手機版調整 + Skeleton 載入態 + 驗收 375px | Step 2–4 |

**先做頁面二**：K 線圖最複雜，建完後整體 Token 和圖表底色就確定了，後面兩頁直接套用。

---

## 已決定的事（前一版待定，現已確認）

1. **API 層**：建皮期間用 Next.js Route Handler（`app/api/stock/[ticker]/route.ts`）直接呼叫 Python subprocess 跑 yfinance，之後 Phase 9 再遷移到 FastAPI。省去建皮階段的 FastAPI 額外複雜度。

2. **圓餅圖**：改用 **shadcn Chart**（`npx shadcn@latest add chart`），底層同為 Recharts，但主題與 CSS 變數自動整合，不需手動對色。
