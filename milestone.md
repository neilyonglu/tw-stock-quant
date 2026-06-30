# 里程碑

> 簡短記錄完成了什麼。細節看 docs/thinking.md，任務清單看 todo.md。

## 2026-06-27 — 環境建置
- Python 3.12 + uv、TA-Lib、twstock、CasualMarket MCP 全部就緒
- 8 個 equity-research AI skills + dispatcher

## 2026-06-28 — Dashboard Step 0–1
- Next.js 16 + shadcn/ui + lightweight-charts 專案建立
- App 框架：sidebar + 三頁路由

## 2026-06-30 — Dashboard Step 2：個股分析頁
- 五層 K 線疊圖、7 種時間週期（5/15/30/60分、日/週/月）
- 公司名稱、Tabs 拆分（K 線圖／速查指標）

## 2026-06-30 — Dashboard Step 3：市場總覽頁
- 指數卡、三大法人、市場廣度、環境結論橫幅（mock）
- 資料合約定型：`lib/types.ts` 對齊未來後端

## 2026-06-30 — 紅漲綠跌色彩修正
- K 線、漲跌文字、三大法人、燈號全面改用台股紅漲綠跌慣例
- 景氣燈號改色點，跟漲跌文字色區隔

## 2026-06-30 — 對照看盤平台補齊功能
- 個股：分時走勢、漲跌停、基本面（PE/PB/殖利率/EPS/52週高低/目標價）、
  籌碼面、五檔報價（真實，twstock.realtime）、新聞、K線型態（mock）
- 市場：大盤分時、櫃買指數、國際指數（真實）、台指期貨、排行榜、新聞快訊、
  成交值/量（mock）
- 修正多處 yfinance NaN 導致 JSON 解析失敗的 bug
