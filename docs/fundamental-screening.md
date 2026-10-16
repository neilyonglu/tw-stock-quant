# 單股基本面研究計算

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
