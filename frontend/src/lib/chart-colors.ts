// 圖表用色的單一來源。lightweight-charts 畫在 canvas 上，吃的是色碼字串而不是 CSS
// 變數，所以不能直接用 globals.css 的 --stock-up/--stock-down token，改由這裡集中管理
// （原本 kline-chart.tsx 與 intraday-chart.tsx 各自複製一份，改配色容易只改到一邊）。
//
// 這裡的值要跟 globals.css 的 `--stock-up` / `--stock-down` 對應；改色時兩邊一起改。
//
// 注意：這組是「圖表」用色。畫面上的**文字**漲跌色另外用 Tailwind 的
// `text-red-400` / `text-emerald-400`，那是依 WCAG 對比度實測選出來的值，
// 跟這裡的圖表色刻意不同，不要為了「統一」而互相取代（見 PROJECT.md 前端慣例）。

// 台股慣例：紅漲綠跌（跟美股的 green-up / red-down 相反）
export const STOCK_UP = "#EF5350" // 漲：紅
export const STOCK_DOWN = "#26A69A" // 跌：綠

// 短週期均線＝amber、長週期均線＝blue；主圖 SMA20/60 與成交量 MA5/10 共用同一套配色慣例
export const MA_SHORT = "#F59E0B"
export const MA_LONG = "#3B82F6"

// RSI 門檻線：PROJECT.md 明訂「非方向性顏色不套紅漲綠跌」。色碼目前與漲跌色相同，
// 但語意不同（這是超買/超賣的水平參考線，不是漲跌方向），所以獨立命名——
// 未來調整漲跌配色時不應該連帶改動這兩條線。
export const RSI_OVERBOUGHT = "#EF5350"
export const RSI_OVERSOLD = "#26A69A"
