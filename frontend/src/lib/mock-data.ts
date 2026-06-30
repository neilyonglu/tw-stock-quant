import type {
  FuturesData,
  MarketOverviewData,
  MarketRankings,
  NewsItem,
  StockChipData,
} from "./types"

// 建皮期間用的假資料，形狀對齊各 interface（見 types.ts 開頭說明，每個 interface
// 上方都標註哪些欄位現在是真資料、哪些是 mock）。

// 加權指數/櫃買指數已搬到 /api/market/indices（yfinance 真資料），這裡只剩還沒接後端的部分。
export const mockMarketData: MarketOverviewData = {
  updated_at: "2026-06-30T13:30:00+08:00",
  business_cycle: { light: "green", label: "綠燈" },
  usdtwd: { value: 31.8, change: -0.3 },
  us10y: { value: 4.35, change: 0.02 },
  institutional: { foreign: 85, trust: 12, dealer: -3 },
  breadth: { up: 650, down: 280, flat: 120, limit_up: 23, limit_down: 2 },
  turnover: { value: 3520, volume: 28.6 },
  environment: { verdict: "多頭", intensity: "積極" },
}

// 台指期貨——plan.md 沒有規劃資料來源，先 mock
export const mockFuturesData: FuturesData = {
  tx_price: 22480,
  tx_change: 35,
  basis: 30, // 正價差：期貨 > 現貨，市場偏多
  foreign_oi: 12500, // 外資淨多單
}

// 排行榜——需要全市場掃描，Phase 1 + Phase 6 做完才能換真的
export const mockMarketRankings: MarketRankings = {
  sector_performance: [
    { name: "半導體業", value: 2.8, unit: "%" },
    { name: "電子零組件", value: 1.9, unit: "%" },
    { name: "航運業", value: 1.2, unit: "%" },
    { name: "金融保險", value: -0.4, unit: "%" },
    { name: "傳產", value: -1.1, unit: "%" },
  ],
  volume_leaders: [
    { ticker: "2330", name: "台積電", value: 312.5, unit: "億元" },
    { ticker: "2317", name: "鴻海", value: 98.2, unit: "億元" },
    { ticker: "2454", name: "聯發科", value: 76.4, unit: "億元" },
    { ticker: "3231", name: "緯創", value: 45.1, unit: "億元" },
    { ticker: "2603", name: "長榮", value: 38.7, unit: "億元" },
  ],
  gainers: [
    { ticker: "6488", name: "環球晶", value: 9.8, unit: "%" },
    { ticker: "3034", name: "聯詠", value: 8.1, unit: "%" },
    { ticker: "2308", name: "台達電", value: 6.5, unit: "%" },
    { ticker: "2379", name: "瑞昱", value: 5.9, unit: "%" },
    { ticker: "2382", name: "廣達", value: 5.2, unit: "%" },
  ],
  losers: [
    { ticker: "2891", name: "中信金", value: -3.2, unit: "%" },
    { ticker: "2882", name: "國泰金", value: -2.7, unit: "%" },
    { ticker: "1303", name: "南亞", value: -2.1, unit: "%" },
    { ticker: "1301", name: "台塑", value: -1.8, unit: "%" },
    { ticker: "2002", name: "中鋼", value: -1.5, unit: "%" },
  ],
}

// 全市場新聞快訊——Phase 6 feedparser 範圍限持倉股，全市場新聞牆要另外找來源，先 mock
export const mockMarketNews: NewsItem[] = [
  { time: "2026-06-30T13:25:00+08:00", title: "台積電法說會釋出樂觀展望，AI 晶片需求持續強勁", source: "經濟日報" },
  { time: "2026-06-30T12:10:00+08:00", title: "外資連 5 日買超台股，加碼半導體類股", source: "工商時報" },
  { time: "2026-06-30T10:40:00+08:00", title: "央行維持利率不變，符合市場預期", source: "中央社" },
  { time: "2026-06-30T09:05:00+08:00", title: "美國 PCE 物價數據優於預期，台股開高", source: "鉅亨網" },
]

// 個股籌碼面——Phase 5 FinMind 才有，先 mock
export function mockStockChip(ticker: string): StockChipData {
  void ticker
  return {
    institutional: [
      { date: "2026-06-26", foreign: 1250, trust: 320, dealer: -80 },
      { date: "2026-06-27", foreign: 980, trust: 410, dealer: 50 },
      { date: "2026-06-28", foreign: -340, trust: 180, dealer: 120 },
      { date: "2026-06-29", foreign: 1560, trust: 290, dealer: -60 },
      { date: "2026-06-30", foreign: 2100, trust: 150, dealer: 90 },
    ],
    margin_balance: 18500,
    margin_balance_change: 320,
    short_balance: 4200,
    short_balance_change: -150,
    big_holder_ratio: 78.4,
  }
}

// 個股新聞——Phase 6 才有真資料來源，先 mock
export function mockStockNews(name: string): NewsItem[] {
  return [
    { time: "2026-06-30T13:20:00+08:00", title: `${name}法說會釋出樂觀展望，外資喊買`, source: "經濟日報" },
    { time: "2026-06-29T16:45:00+08:00", title: `${name}5 月營收創新高，年增逾 15%`, source: "MoneyDJ" },
    { time: "2026-06-27T09:30:00+08:00", title: `法人連 3 日買超${name}，籌碼面轉強`, source: "工商時報" },
  ]
}
