# 基本面資料交叉核對（2026-10-16）

範圍：本機 `data/raw/fundamentals/2330/`、`6488/` 的 FinMind 快照。
這是科目抽查，沒有逐列驗證五張表，也沒有驗證所有股票；不據此宣稱資料完全正確。

## 指定參考專案

檢查 [clsung/tw-stock-agent](https://github.com/clsung/tw-stock-agent/tree/c163d1d92b48bc813df49cbbf1419172fabbb85e)
實際程式，而非只按 README 的功能描述判斷：

- [stock_service.py](https://github.com/clsung/tw-stock-agent/blob/c163d1d92b48bc813df49cbbf1419172fabbb85e/tw_stock_agent/services/stock_service.py)：`fetch_stock_data` 讀 twstock 代碼表，回名稱、上市櫃、產業等；價格、即時與四大買賣點也用 twstock。
- [data_fetcher.py](https://github.com/clsung/tw-stock-agent/blob/c163d1d92b48bc813df49cbbf1419172fabbb85e/tw_stock_agent/utils/data_fetcher.py)：`fetch_monthly_price` 是股票某月份的每日行情，不是公司月營收。
- [mcp_server.py](https://github.com/clsung/tw-stock-agent/blob/c163d1d92b48bc813df49cbbf1419172fabbb85e/mcp_server.py)：公開工具為基本資料、歷史價格、即時價格、技術分析與市場概況，沒有三張財報、月營收、股利或 ROE／F-score。

因此它可參考行情處理與上市櫃辨識，但無法作為此次基本面數值的交叉來源。
上市櫃資料若雙方同用 twstock，也不是獨立來源驗證。不新增 MCP 依賴或照搬其快取／錯誤處理架構。

## 改用公司原始公告抽查

| 科目／期間 | 本機 FinMind 原始值 | 官方對照與結果 |
|---|---:|---|
| 2330，2026 Q2 EPS | 27.25 元 | 官方公布稀釋 EPS 27.25；數值相同，但仍須保留基本／稀釋口徑差別 |
| 2330，2026-06-30 總資產 | 9,375,654,727,000 元 | 官方 9,375,655 百萬元；按官方顯示精度相符 |
| 2330，2026 上半年營業現金流 | 1,482,341,242,000 元 | 官方 1,482,341 百萬元；按顯示精度相符，為累計半年值 |
| 2330，2026 年 9 月營收 | 511,857,399,000 元 | 官方申報 511,857,399 千元；換算後精確相同 |
| 6488，2026 Q2 基本 EPS | 7.90 元 | 官方單季基本 EPS 7.90；相符，半年基本 EPS 則為 11.87 |
| 6488，2026 Q2 營收 | 15,214,310,000 元 | 官方單季 15,214,310 千元；相符 |
| 6488，2026-06-30 總資產 | 219,220,426,000 元 | 官方 219,220,426 千元；相符 |
| 6488，2026 上半年營業現金流 | 2,812,066,000 元 | 官方 2,812,066 千元；相符，為累計半年值 |
| 6488，2026 年 9 月營收 | 5,128,632,000 元 | 官方網頁 5,129 百萬元；按顯示精度相符 |
| 6488，2025 下半年股利 | 5.7 元／股 | 官方簡報 5.7，2026-07-22 基準日、08-14 發放日與原始列相符；基準日不是除息日 |

對照來源：

- [台積電 2026 Q2 財務報表](https://investor.tsmc.com/english/encrypt/files/encrypt_file/reports/2026-07/114aaca0fea2050e96b91fffbab9ed04ba09cd92/FS.pdf)，第 1、2、4 頁。
- [台積電 2026 年 9 月營收申報（SEC）](https://www.sec.gov/Archives/edgar/data/1046179/000104617926000680/tsm-revenue20261008.htm)，千元欄位。
- [環球晶 2026 Q2 合併財報](https://www.sas-globalwafers.com/wp-content/uploads/2026/05/GlobalWafers_2026Q2-consolidated-financial-statement_CN.pdf)，PDF 第 4、5、7、29 頁。
- [環球晶財務情報](https://www.sas-globalwafers.com/investor-jp/financial-information-jp/)，2026 月營收表。
- [環球晶 2026-03-11 官方簡報](https://www.sas-globalwafers.com/wp-content/uploads/2026/03/GWC_company-profile_20260311-EN.pdf)，第 6 頁。

## 已發現的限制與差異

1. **資料更新落後公告**：本機 2330 損益表最後為 2026-06-30，但公司已於
   [2026-10-15 公告 Q3](https://www.sec.gov/Archives/edgar/data/1046179/000104617926000726/a3q26e_withguidancexfinal.htm)。
   先前「最新 Q2」僅指此次來源取得的最後一期，不是公司最新公告。
   `fetched_at` 很新也不能證明財報期別最新，後續計算要揭露實際期間及更新狀態。
2. **EPS 未完全一致**：6488 的 2025-12-31 EPS 為 4.61，官方 2026-03-11 簡報 Q4 為 4.60，
   相差 0.01。官方亦提醒季度與全年 EPS 的加權股數不同，不能直接相加；
   此次尚未確認該筆差異原因，不擅自改數值、不直接認定是四捨五入。
3. **季營收有小額差異**：2330 的 2026 Q2 `Revenue` 為 1,270,380.25 百萬元，
   官方 Q2 財務報表為 1,270,381 百萬元，相差 0.75 百萬元，不能說是同一值按百萬元四捨五入。
   原始值恰等於本機 4–6 月營收合計，但不足以證明差異原因；保留來源值並列為待查。
4. **期間不能直接混算**：上述損益科目為單季，現金流為年初至期末累計。
   例如 2330 Q2 單季營業現金流應以半年累計減 Q1，得到 783,364,977,000 元，
   與官方的 783,365 百萬元按顯示精度相符；不能拿半年現金流除以單季淨利計算 FCF 轉換率。
5. **科目必須以資料表區分**：`EquityAttributableToOwnersOfParent` 在損益表為歸母淨利，
   在資產負債表為歸母權益；`_per` 欄位是百分比，不能當金額。
   EPS、每股股利、股數、金額與比率不能套同一單位轉換。
6. **日期不能代替公告時間**：9 月營收的 `date` 是 10 月 1 日，所屬月要讀
   `revenue_year`／`revenue_month`；`create_time` 是入庫日。財報期末、股利基準日、
   除息日、發放日各有不同意義，不能都拿來當歷史回測的可知日期。

結論：原始資料入口可用，但不具備「所有科目皆正確且為最新」的保證。
本次保留原始資料，不以公告值靜默覆寫來源。基本面計算前須處理期間、缺值、更新狀態，
並追查上列 EPS 與季營收差異；尚未實作自動公告比對、資料差異阻擋或完整 point-in-time 資料集。
