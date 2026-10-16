# 單股基本面研究計算

## 這次做了什麼、畫面哪裡不同

這次完成的是資料與後端研究計算，**網站目前沒有新增可見畫面**。
前端尚未呼叫這組基本面計算，所以重新整理個股頁或選股頁不會看到新增 ROE／F-score。

| 位置 | 現況 | 本次新增結果在哪裡看 |
|---|---|---|
| 個股 → 基本面：PE／PB／殖利率／EPS 等卡片 | 維持既有 yfinance profile；EPS 仍是近 12 個月值 | 新的四季 EPS 與 TTM ROE 在下面的研究 CLI，不是卡片既有 EPS |
| 個股 → 基本面：月營收表 | 仍是有示範標記的 mock，沒有換成 FinMind | 真實月營收原始值可查中台，三個月 YoY 可看研究 CLI |
| 每週選股頁 | 仍是多因子與投組示範資料 | 尚未將本次單股研究結果接入 |
| 中台 http://localhost:8001/docs | 新增 fundamentals 原始資料路由（須載入本分支中台） | 可選股票、資料類型及期間，查看原始資料 |
| PowerShell／終端機 | 新增品質檢查與研究計算指令 | 下節指令回傳 JSON |

本分支尚未 push／merge／部署，server 不會因本機提交就自動更新。
之後接前端時，需要替月營收換真、呈現期間／來源品質、加入指標說明；不能把未完整的 F-score
顯示成 0 分或合格，也不能把研究條件直接當成每週多因子選股結果。

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
F-score 的 known_signals=7 是可計算七項，不是七分，也不是 7/9 合格。

2026-10-16 驗收時，6488 的四季 EPS 均正、TTM ROE 約 10.85%、9 月營收 YoY 約 -13.13%；
ROE 與三個月營收門檻未符合，但因 F-score 仍缺資料且來源未全面驗證，整體仍是 incomplete／passed=null。
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
| 系統整體狀態及接下來缺什麼 | [PROJECT.md](../PROJECT.md)、[todo.md](../todo.md) |

驗證：104 項 Python 測試通過，含公式、分母、連續期間、缺值、F-score 九項、品質限制與 client；
2330／6488 CLI 經本機中台實際抓取驗證。Docker 是用現有正式映像唯讀掛入本分支 backend 與
本機快照，離線確認相同研究流程可執行，不代表 server 已部署或新映像已完成正式 CI。

## 計算入口

啟動本分支中台後執行：

```bash
uv run python -m backend.api.screen_fundamental 6488
```

CLI 共用 check_fundamentals 的 raw client，從 DATA_SERVICE_URL（預設 http://localhost:8001）
取損益、資產負債、現金流與月營收四張表。外部資料仍只由中台抓取；前端尚未改接。
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
現有來源缺可靠普通股發行紀錄及完整長債口徑（含租賃等問題），adapter 對這兩項回 null，
不拿部分公司債／借款或全部非流動負債代替。兩檔目前各可計算七項，完整總分尚不可用。
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
