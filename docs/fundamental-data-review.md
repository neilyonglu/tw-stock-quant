# 基本面資料交叉核對（2026-10-16；營收參考值於2026-10-20更正）

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
| 2330，2026 Q2 營收 | 1,270,380,250,000 元 | 完整核閱財報為 1,270,380,250 千元；換算後精確相同 |
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

- [台積電 2026 上半年完整核閱合併財報](https://investor.tsmc.com/sites/ir/financial-report/2026/TSMC%202026Q2%20Consolidated%20Financial%20Statements_E_2.pdf)，印刷頁4／PDF第5頁，2026年第二季營收欄位，單位千元。

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
   2026-10-20確認該Q3公告為業績摘要，註明數字尚未經董事會通過；公告種類記為 `earnings_release`，不等同完整核閱財報。
   直接API及全新中台程序均僅取得Q2；Q3指定日期與不設迄日查詢均無資料。警示揭露摘要已公布及來源實際期間，不推定FinMind遺漏完整財報。
2. **EPS 已補正式財報核對**：6488 的 2025-12-31 EPS 為 4.61，簡報 Q4 顯示 4.60。
   後續查 [2025 年度財報](https://www.sas-globalwafers.com/wp-content/uploads/2025/11/FY2025_GlobalWafers-Financial-Statement_consolidated-CH.pdf)
   的基本 EPS 15.29，及 [前三季財報](https://www.sas-globalwafers.com/wp-content/uploads/2025/11/GlobalWafers_2025Q3-consolidated-financial-statement_CN.pdf)
   的累計基本 EPS 10.68，相減可重現 4.61。兩期加權平均股數按千股顯示同為 478,114；
   歸母年度淨利 7,312,028 千元減前三季 5,107,216 千元，再除該股數亦約為 4.61148。
   參考紀錄改用正式財報推導值 4.61，原始值不改寫；簡報為何呈現 4.60 未獲公司說明，
   不宣稱已確認其產生原因。此個案不代表所有公司的 EPS 可直接相減或相加。
3. **季營收參考值已更正（2026-10-20）**：2330 的 2026 Q2 `Revenue` 為 1,270,380,250,000 元，
   完整核閱合併財報單季營收為 1,270,380,250 千元，換算後與 FinMind 精確相同。
   先前採用的法說簡明報表顯示 1,270,381 百萬元；兩份公司文件差異原因未確認，不能當作同一值四捨五入。
   參考值及來源改用完整核閱財報、精度為千元，保留簡明文件作歷史對照，不改 FinMind 原始值。
   原日期區間、單季區間及單日期三次 API 查詢均回同一筆 Revenue，排除這三組日期設定造成此筆差異。
   月營收查4/1～6/30會取得所屬月3～5月；查5/1～7/1才取得4～6月，合計亦相符。
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
季營收參考值已依完整核閱財報更正；尚未實作自動公告比對或完整 point-in-time 資料集。

## 計算層品質檢查

啟動本分支中台後，在根目錄執行：

```bash
uv run python -m backend.api.check_fundamentals 2330
uv run python -m backend.api.check_fundamentals 6488 income_statement
uv run python -m backend.api.check_fundamentals 6488 monthly_revenue
```

沿用 DATA_SERVICE_URL（預設 http://localhost:8001），每次只查指定一張表，
交給 `backend.screening.fundamental_quality.assess_fundamentals()` 回品質摘要。
不新增中台 HTTP contract、不改原始值，也不回股票合格／不合格或投資分數。

| status | 意義 | can_screen |
|---|---|---|
| pending_update | 來源落後人工確認的公告期間 | false |
| needs_review | 抽查值不符、缺值或有多筆候選值 | false |
| missing_data | 沒有資料／中台回 404，不等於股票不合格 | false |
| invalid_data | 結構、來源、股票、日期或數值不合法 | false |
| source_error | 中台連線、限額或其他來源錯誤 | false |
| service_outdated | 中台沒有新路由，確認 DATA_SERVICE_URL 並重啟本分支中台 | false |
| unverified | 沒有上述阻擋，仍未全面驗證 | null |

can_screen 尚無任何情況回 true；null 不能當已驗證通過。
latest_period 是實際期間，月營收使用所屬年月首日；period_basis 分別為
quarterly／point_in_time／year_to_date／monthly／distribution_record。
此步不把累計現金流轉成單季，必要科目與連續期間仍由後續指標驗證。

`backend/data/fundamental_references.json` 保存此次人工公告及三筆比較，包含科目、期間、
口徑、單位、參考值、顯示精度、來源種類與網址。以 Decimal 按顯示精度四捨五入比較，
沒有任意百分比容差；營收採完整核閱財報的千元精度。簡報差異保留紀錄，
不會覆寫來源或自動選成權威值。人工紀錄更新時需重新查證原始文件。

freshness=unknown 表示沒有適用的人工公告紀錄；at_least_reviewed_period 只表示
不落後該筆紀錄，不代表目前最新。查詢結束日以後的公告不列入更新要求，
區間外的歷史比較也不阻擋本次查詢；這不提供歷史可知時間保證。
若同時落後公告與數值有差異，主狀態為 pending_update，checks／issues 仍保留所有問題。
尚未自動追蹤全部公告；EPS 及此筆季營收已補正式財報核對，更新落後與其他缺項仍獨立阻擋。
基本面研究計算與 F-score 缺項限制見 [計算規格](fundamental-screening.md)。

若舊版中台未重啟，新增路由會回 FastAPI 的 404 Not Found，並非 FinMind 查無財報。
CLI 會區分此情況與真正沒有資料的 404。先停止原本的本機中台，再執行
`uv run uvicorn backend.data_service.main:app --reload --host 127.0.0.1 --port 8001`；
`--reload` 可在後續改動 Python 時重新載入。若使用 Docker 或自訂 DATA_SERVICE_URL，
需更新該服務；啟動另一個服務不會改變 CLI 原先指向的位址。

## 官方年度文件批次查證

啟動本分支的中台後執行：

```bash
uv run python -m backend.api.audit_financials 2409 3481 1303 --year 2025
uv run python -m backend.api.audit_financials --all --year 2025
```

使用 Docker 時，可直接在已更新的本機中台容器執行，報告保存在既有 data volume：

```bash
docker compose -p tw-stock-quant exec -w /app data-service python -m backend.api.audit_financials 2409 3481 1303 --year 2025
```

`--all` 使用本機 twstock 一般上市／上櫃股票名單，不含 ETF。預設僅查指定股票，年度限
2019 起已結束年度；不是保證該年度文件已公告。沿用 `DATA_SERVICE_URL`。
每家公司間隔 6 秒，串行查詢；上游限流（429／503）會停下並列出 `remaining`，不持續重試。
舊中台沒有新路由時標為 `service_outdated` 並停止，先重建／重啟中台再執行。
來源額度、可用性及名單更新仍須依實際環境處理。

預設輸出 `data/processed/official-audit-2025.jsonl`，逐公司寫入並 flush；
相鄰 `.exceptions.json` 依科目／錯誤種類合併公司，包含已處理家數、官方文件快取命中數及
未完成公司。可用 `--output` 指定路徑。重新執行會重建這兩個報告，但中台保存的原件不受影響。

中台是唯一對外取資料的地方：從 MOPS 取得年度合併 inline XBRL，保存在既有 SQLite
`official_filings`，包含來源網址（可重建）、SHA-256、取得時間與原始位元組；不同內容保留版本。
已解析有效的最新文件快取 24 小時，`--refresh` 強制重新下載；無效文件保留作追查，不視為有效快取。
因此重跑不用重抓有效官方文件；FinMind 則沿用原本 1800 秒記憶體快取，重啟後仍需重新查詢。
中台需使用此分支版本；舊版 Docker 需要重建映像並重啟，不能只重跑 CLI。

目前抽取非流動長期借款、公司債及租賃三個指定 XBRL 科目，涵蓋當年及前年年底。
嚴格檢查公司、年度、合併口徑、無維度期末 context、TWD 單位、格式與 scale；
UTF-8 無法嚴格解碼才改 CP950，沒有以替代字元掩蓋錯誤。
缺少標籤留 `missing_data`，不推定零；多筆候選留 `ambiguous_data`，不挑第一筆。
其他標籤別名、金融業、不同會計年度或報表格式尚不支援，應列例外後補共通映射。

計算層比對 FinMind 同股票、同日期的長期借款／公司債原值，完全相等才標 `matched`；
不相等或多筆標 `needs_review`。租賃目前只保存官方抽取結果，未宣稱交叉驗證。
共同缺項以一組例外處理，不必逐公司手填。

所有結果 `can_screen=false`、`equity_issued=null`，抽取狀態 `extracted_unverified`。
本流程尚未涵蓋普通股發行及全部年度 F-score 輸入，沒有自動覆寫人工補充或改動選股分數；
借款／公司債相符也不表示整份財報或股票已全面驗證。

實際驗證：2409／3481／1303 的 2025 年報共 8 筆借款／公司債比較與 FinMind 相符；
三家公司重跑均命中官方原件快取。友達／群創公司債標籤未取得，三檔普通股發行仍未知。
