# 單股基本面研究計算

## 這次做了什麼、畫面哪裡不同

資料、後端研究計算與個股「基本面」頁已串接。本機預覽可開
http://localhost:3109/stock/6488 ，點「基本面」。預覽服務未執行時，可在 frontend 執行
`npm run dev -- --port 3109`，並確認中台 8001 已啟動；避免與 Forge 的 3000 衝突。

| 位置 | 現況 | 本次新增結果在哪裡看 |
|---|---|---|
| 個股 → 基本面：PE／PB／殖利率／EPS 等卡片 | 維持 yfinance profile；有效零 EPS／零殖利率已保留 | EPS 明確標示近 12 個月，與新四季 EPS 區分 |
| 個股 → 基本面：研究區塊 | 新增 TTM ROE、四季 EPS、年度 F-score 與九項訊號 | 附公式說明、實際期間、條件狀態及來源限制 |
| 個股 → 基本面：月營收表 | 已改成 FinMind 真實最近六個連續月份 | 金額由元換算億元，YoY 由計算層算，缺值顯示 —，已刪除月營收 mock |
| 每週選股頁 | 仍是多因子與投組示範資料 | 尚未將本次單股研究結果接入 |
| 中台 http://localhost:8001/docs | 新增 fundamentals 原始資料路由（須載入本分支中台） | 可選股票、資料類型及期間，查看原始資料 |
| PowerShell／終端機 | 新增品質檢查與研究計算指令 | 下節指令回傳 JSON |

server 不會因本機提交就更新，需經 push／PR／合併 main 與 CI 才會部署。
依使用者要求，同一功能分支做到前端並驗收後才交 PR，不先合併只有後端的版本。
不完整的 F-score 顯示 — 及可計算項數，不能顯示成 0 分或合格；研究條件不是每週多因子選股結果。

## 操作與閱讀結果

在專案根目錄執行。需要已啟動本分支中台；若 8001 正在執行，不要再開第二個佔用同埠的服務。

```powershell
# 只檢查資料品質：是否有已知更新延遲或人工核對差異
uv run python -m backend.api.check_fundamentals 2330

# 計算四項研究門檻並保留資料限制
uv run python -m backend.api.screen_fundamental 6488

# JSON 太長時，只列出每項條件的狀態
$result = uv run python -m backend.api.screen_fundamental 6488 | ConvertFrom-Json
$result.rules | Select-Object id, status, condition_met
```

讀取順序：先看 status／reason，再看 rules 各項的 status 與 value，最後看 inputs 使用哪個
期間與科目。condition_met 是公式算出的條件符合度；passed 是已驗證合格判定，現階段保持 null。
F-score 的 known_signals=7 是可計算七項，不是七分，也不是 7/9 合格；兩檔已補資料的年度可回完整分數。

2026-10-16 驗收時，6488 的四季 EPS 均正、TTM ROE 約 10.85%、9 月營收 YoY 約 -13.13%；
ROE 與三個月營收門檻未符合，F-score 為 2025 年度 5/9，研究條件亦未符合 >= 6；
整體為 calculated_unverified／passed=null，因為來源未全面驗證，不能宣稱已驗證選股結論。
2330 所取得財報只到 Q2，而人工紀錄已知公告 Q3，依賴最新季度的條件因此為 pending_update。
這是當次資料快照，之後來源更新時應以新輸出及其期間為準。

## 文件與程式對照

| 想問的問題 | 回查位置 |
|---|---|
| 資料從哪裡來、五類資料如何查、token 怎麼設定 | [中台合約](../backend/data_service/README.md#基本面原始資料) |
| 怎麼知道資料有差異、哪些已解決或待查 | [核對紀錄](fundamental-data-review.md)；backend/data/fundamental_references.json |
| EPS／ROE／YoY／F-score 怎麼算 | 本文件下方公式；backend/indicators/fundamental.py |
| 門檻、期間、缺值與品質如何影響結果 | 本文件下方品質說明；backend/screening/fundamental.py |
| 終端機如何取資料與呼叫計算 | backend/api/check_fundamentals.py、backend/api/screen_fundamental.py |
| 前端如何接線 | frontend/src/app/api/stock/[ticker]/fundamentals/route.ts；frontend/src/components/stock/fundamental-panel.tsx |
| 完整長債與普通股發行怎麼補 | backend/data/fundamental_supplements.json；下方年度補充規則 |
| 系統整體狀態及接下來缺什麼 | [PROJECT.md](../PROJECT.md)、[todo.md](../todo.md) |

驗證：110 項 Python 測試、TypeScript 與正式前端建置通過。瀏覽器驗證 6488 實際數值、
桌面與 375px 無橫向溢出、來源失敗／重試、6488→2330→2317 搜尋切換不殘留分數。
完整 Docker image 另以 fundamental-preview 標籤建置，不影響既有 latest 與正式容器；
隔離容器端到端驗證前端、中台與 FinMind 的實際資料流程，並確認中台停止時前端 API 回傳 503。
容器互通驗收與 server 部署是不同事項，main CI／部署仍需在合併時確認。

## 計算入口

啟動本分支中台後執行：

```bash
uv run python -m backend.api.screen_fundamental 6488
```

CLI 共用 check_fundamentals 的 raw client，從 DATA_SERVICE_URL（預設 http://localhost:8001）
取損益、資產負債、現金流與月營收四張表。外部資料仍只由中台抓取。
Next `/api/stock/{ticker}/fundamentals` 透過既有 runPythonModule 執行同一研究 CLI，
最多等候 180 秒，取消請求時傳遞 AbortSignal；既有行情子程序維持 30 秒預設。
profile 與研究區塊各自載入，任一來源失敗不遮掉另一區；切換股票立即重設狀態。
純計算在 `backend/indicators/fundamental.py`，期間／門檻組合在 `backend/screening/fundamental.py`。

## 三項基本條件

門檻沿用 plan.md，不新增權重。

| 條件 | 本版定義與限制 |
|---|---|
| 四季 EPS 均 > 0 | 從損益表最後一期往前四個連續曆年季末，基本 EPS 分別判斷，零與負值不符合，不跳缺季、不加總成 TTM EPS |
| ROE > 12% | 近四季合併 IncomeAfterTaxes 合計 ÷ 期初期末平均合併 Equity × 100；需要一年前與本期期末權益且兩者 > 0 |
| 三個月 YoY 均 > 0% | 最近三個連續所屬月，各算 (本月營收 ÷ 去年同月營收 − 1) × 100；去年為零、負值或缺值無法計算，當期零營收為 -100% |

ROE 採 TTM 研究定義，不是單季乘四，也不保證與使用平均季末權益或歸母口徑的平台相同。
公式方向參考 [公開資訊觀測站說明](https://mopsfin.twse.com.tw/terms)，本版另明訂四季與期初期末平均。
不把歸母淨利配合合併總權益，也不混算單季與累計。

## F-score

`piotroski-ifrs-v1` 使用最近已完成年度及前一年度；原始研究見
[Piotroski (2000)，第 7–10 頁](https://www.ivey.uwo.ca/media/3775523/value_investing_the_use_of_historical_financial_statement_information.pdf)。
採四季合併本期淨利合計作年度 NI，是 IFRS 研究映射，不冒稱美國原始資料庫的 extraordinary-items 科目。
年度 CFO 直接取 12 月底累計值，資產負債使用年底快照。九項各一分：

1. NI／期初資產 > 0。
2. CFO／期初資產 > 0。
3. ROA 提高。
4. 同年度 CFO > NI。
5. 長債／期初期末平均資產下降。
6. 年底流動比率提高。
7. 當年沒有發行普通股，需明確事實，不能由空白、股本或股數變化猜測。
8. 年度毛利率提高。
9. 年度營收／期初資產的周轉率提高。

相等不算改善；各項 true／false／null，九項都有資料才回總分。
缺項時 score=null；known_signals 是可算幾項，**不是分數**，不能用小計判定 >= 6。
FinMind 缺少完整長債與發行紀錄，已對 2330、6488 的 2025／2024 官方合併財報人工核對補充，
保存在 `backend/data/fundamental_supplements.json`。長債定義為非流動公司債帳面金額、
非流動長期借款與非流動租賃負債之和，排除一年內到期、遞延稅負及其他非借款負債。
不拿還款現金流當負債餘額，不把全部非流動負債代替長債。

| 股票／年度 | 公司債 | 借款 | 租賃 | 長債合計（新台幣千元） |
|---|---:|---:|---:|---:|
| 2330／2025 | 856,227,503 | 39,834,496 | 31,594,992 | 927,656,991 |
| 2330／2024 | 926,604,506 | 31,824,386 | 28,755,342 | 987,184,234 |
| 6488／2025 | 35,679,196 | 7,564,868 | 649,360 | 43,893,424 |
| 6488／2024 | 27,147,373 | 10,530,658 | 749,455 | 38,427,486 |

來源與證據在補充檔逐筆附網址與說明：
2330 使用 [官方 XBRL 年度合併報表](https://mopsov.twse.com.tw/server-java/t164sb01?step=1&CO_ID=2330&SYEAR=2025&SSEASON=4&REPORT_ID=C)，
6488 使用 [官方年度合併財報](https://www.sas-globalwafers.com/wp-content/uploads/2025/11/FY2025_GlobalWafers-Financial-Statement_consolidated-CH.pdf)
PDF 第 8／10／12／44 頁。環球晶租賃非流動金額在附註，不能用流動加非流動合計。
普通股發行核對完整權益變動、現金增資與股份基礎給付欄，兩檔 2025 為未發行；
6488 的 2024 明列普通股增資，不是由股本淨變動推測。

補充只按股票及年度精確匹配，不改 FinMind 原始值；新年度、其他股票不沿用舊值。
這是人工維護的有限驗收資料，沒有自動抓取全部官方財報。畫面會標示人工核對與日期。
驗收兩檔可計算九項（2330／2025 為 9 分，6488／2025 為 5 分）；2317 仍無完整核對，總分 null。
金融、保險、證券及金控產業不套用此一般產業 F-score。

## 品質與結果

每項 rule 帶 value、inputs、status、condition_met、passed 與 reason。
value 可保留有品質限制的計算值供檢查，必須一起讀 status／reason。
必要來源落後公告或所用科目／期間有差異時，condition_met=null；
完成舊年度的 F-score 不因最新季度落後就誤判缺少那一年度。
缺資料不補零、不默默換更舊期間；來源錯誤不等於股票不合格。

calculated_unverified 只表示已依公式計算，未全面驗證來源。各 rule.passed 及整體 passed
保持 null，不將未知資料宣告已驗證合格。任一條件未知時 conditions_met=null、status=incomplete；
否則可顯示研究條件合取值，仍非已驗證選股結論。沒有全市場排名、歷史可知時間資料或前端整合。
原始資料、EPS 正式財報核對與未解季營收差異見 [資料核對](fundamental-data-review.md)。
