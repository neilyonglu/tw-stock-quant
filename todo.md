# 待辦

> Dashboard 建皮（Step 0–5）已全部完成，成果見 `PROJECT.md`。Phase 1–8 細節見 `plan.md`。
> 分工（2026-07-23 與隊友確認）：隊友 branch 只做**回測系統**；技術指標、選股評分、投組優化歸本專案。

## 現在就可以做（不依賴隊友）

- [x] 全庫審查後修正行情 Decimal 價格、還原失敗狀態持久化與跨週期快取失效、有界 TTL 快取、基本面未來月份及重複財報攔截，並同步現況文件（2026-10-21）。
- [x] 前端審查 FE-01–07：市場環境標示示範、分時／五檔刷新與時間、選股失敗重試、自選股儲存失敗提示、換股網址同步、刷新保留 K 線視窗及搜尋無障礙；固定 API 測試資料的 Chrome 互動驗收通過（2026-10-21）。
- [x] Python 目錄統一為 backend/api 與 backend/data_service，更新啟動／Docker／測試路徑；Archify 升級 3.1.0，架構說明見 docs/ARCHITECTURE.md
- [x] 現有 main 的 Docker／CI／tw-stock runner 部署設定（獨立 feature/main-deployment 分支，不帶入指標新功能）
- [x] main 雲端 CI 與 tw-stock runner 自動部署成功；容器改名 PR #5 已合併，2026-10-13 的 main run 38337855813 成功
- [x] 目錄整理與架構圖 PR #6 已合併 main；本機與遠端 refactor/backend-layout 已刪除
- [x] 中台快取持久化（SQLite）——2026-07-23 完成，最終狀態見 PROJECT.md 架構段
- [x] 自選股清單＋市場/個股頁面定期自動刷新——2026-07-29 完成（branch `feature/watchlist-live-refresh`），最終狀態見 PROJECT.md
- [x] 自選股頁改 App 風格（sparkline）＋個股首頁排行榜（示範資料）＋K 線今日按鈕——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 查無股票代碼錯誤畫面＋股票關鍵字搜尋＋修切換代碼殘留舊資料 bug——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 全 repo 稽核＋修掉三條「假資料看起來像真的」——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] 稽核其餘 11 項全部修完（白屏防護、漲跌停算錯、RSI 演算法、缺值語意、快取加鎖等）——2026-07-29 完成，同上 branch，最終狀態見 PROJECT.md
- [x] Route Handler 改 `uv run` 執行 Python（Windows PATH 踩坑）——2026-09-20 完成，同上 branch；副作用：TA-Lib 環境障礙消失，見 PROJECT.md「Python 環境」
- [x] `feature/watchlist-live-refresh` 已於 2026-09-22 經 PR #3 合併 main
- [ ] 決定 `.agents/`（archify skill 本體）與 `skills-lock.json` 要進版控還是 `.gitignore`——目前是 untracked；隊友要共用同一份 skill 就 commit，否則 ignore 各自 `npx skills add`
- [x] 個股頁指標說明、週期提示、缺值與位置判讀修正；收尾後共 23 個 Python 測試、Node 檢查與桌面／手機驗證通過
- [x] 指標收尾：KD／ATR 圖表與速查、還原失敗 503／隱藏／恢復、23 項測試及公開算法／參考數值對照；詳見 docs/indicator-review.md
- [ ] 指定券商畫面逐筆驗收：需同批行情與還原／週期／起始時間設定；目前已記錄算法差異，不宣稱各平台預設值相同
- [x] `feature/indicators-module`（Phase 2）完成 rebase、驗證及推送，已開 [PR #7](https://github.com/neilyonglu/tw-stock-quant/pull/7)
  - 指標與測試已適配 backend/indicators，Python 改以 backend.api.get_stock_data 模組執行。
  - 保留 main 的 Docker／CI 設定，排除原分支上重複的舊部署提交。
  - CI 改跑 pytest，涵蓋指標測試與既有個股 JSON／資料庫位置檢查。
- [x] PR #7 已合併 main，遠端與本機 feature/indicators-module 已刪除
- [ ] 確認 PR #7 合併版本的 main CI 與 server 部署結果（與功能測試分開驗收）
- [x] `feature/stock-universe`：共用一般股票清單與 `.TW`／`.TWO` 解析，涵蓋 K 線／分時／基本面／快取鍵；31 項測試與兩市場實際來源、Docker smoke check 通過
- [x] `feature/stock-universe` 經 PR #8 合併 main，本機與遠端分支已刪除；server 部署另依 Actions 驗收
- [x] `feature/technical-screening`：單股日 K 技術規則、分數、各項理由、真實交叉與品質阻擋；55 項測試、2330／6488 真實中台與正式 Docker CLI 通過
- [x] technical-screening 已經 PR #9 合併 main，遠端分支已刪除
- [ ] 確認 PR #9 的 main CI／server 部署結果；本機已合併的舊 technical-screening 分支尚待清理
- [x] `feature/fundamental-data`：中台接入 FinMind 三張財報、月營收與股利；73 項測試及 2330／6488 五類真實 HTTP 資料驗證通過，快照只留本機 data/raw
- [x] 基本面品質檢查與 CLI：依人工公告標示待更新／待核對／尚未驗證，保留實際期間、比較精度與來源，不覆寫原始值或假判合格
- [x] 基本面研究計算：TTM ROE、四季 EPS、三月營收 YoY、四項門檻與理由及 F-score 九項純計算；104 項測試與兩檔 CLI／Docker 通過，passed 仍為 null
- [x] 6488 2025 Q4 EPS 4.61 用正式年度／前三季累計 EPS 及歸母淨利差額核對，修正人工參考，不覆寫原始值
- [x] 2330／6488 2025／2024 年度 F-score 缺項用官方合併財報人工核對補齊，保留長債組成／發行證據／來源／日期，其他股票與年度不沿用
- [x] 官方年度財報批次取得／SQLite 原件快取／FinMind 借款及公司債比對／合併例外報告；優先驗證友達、群創、南亞，未自動補值或完成全市場 F-score
- [x] 普通股年度變動證據：保留兩年度完整普通股維度明細與勾稽、抽取明確增資事件；五家十年度實際核對，環球晶 2024 增資可辨識，未由缺列或股本不變判定未發行
- [x] 友達／群創 2025／2024 完整官方合併 PDF 核對零公司債、非流動借款／租賃及未發行母公司普通股；逐筆來源 SHA／頁碼／日期入補充表，兩檔 2025 年度九項齊備且均為 7／9，原始 XBRL 缺值仍不自動改零
- [ ] 擴大可靠年度資料來源與自動更新，處理金融業模型及全市場完整已驗證基本面名單；目前不是所有股票都有完整 F-score
- [x] 2330 2026 Q2 營收改用完整核閱財報參考值，與 FinMind 精確相符；公告警示區分業績摘要與完整核閱財報，115 項測試與實際 API 驗證通過
- [x] 2330 公告自動追蹤：最近兩季業績公告及最近四個月營收公告，依公告日期截止；保留 raw、null、人工參考，公告已出但資料未更新時保守標示 `pending_update`。`scripts.check_announcements` 通過，實際抓取兩類均 available：2026-09-30 業績期於 2026-10-15 公布、2026-09 營收於 2026-10-08 公布
- [x] 擴充 2409／6488／3481 官方近期公告追蹤，區分日期／期間、GWC 6488／SAS 5483 及業績摘要／完整報表；3481 改用官方 EN/ir 近期新聞 API（空白 year），驗證欄位及文章來源。讀取上限 4,000,000 bytes、逾時 5 秒；修正 GWC Q1 正文寫法誤判。152 項 pytest、checker 與四家八組實際抓取皆 available（2026-10-22）；近期 feed 不保證歷史完整。
- [ ] 基本面資料核對後續：自動公告支援 2330／2409／6488／3481 四家近期來源，其他股票仍 unsupported；近期頁不保證歷史或月報連續完整。Q3 業績摘要已公布但 FinMind 目前僅 Q2，最新期別條件仍暫不判定。全市場公告追蹤、可靠年度資料來源與自動更新、金融業模型及全市場完整已驗證基本面名單仍未完成；見 docs/fundamental-data-review.md
- [x] 修正 profile 零 EPS／殖利率與非有限數值；基本面前端接真實六個月營收／YoY、四季 EPS、ROE、F-score／九項訊號、資料品質與來源；110 項測試與前端建置、桌面／手機／失敗重試／切股驗證通過
- [ ] 基於股票清單做批次掃描與頻率控制，批次套用已完成的單股技術規則；尚未產生全市場真實排行榜或多因子評分
- [ ] 選股評分與投組優化（Phase 藍圖見 plan.md）；完成後 `/api/screening` mock 換真、`frontend/src/lib/types.ts` 合約對齊
- [ ] 前端剩餘 mock 欄位換真實 API：三大法人、市場廣度、排行榜、籌碼 Tab 等（完整清單見 PROJECT.md 真實 vs mock 對照表；依賴各 Phase 資料源接入）
- [ ] `main.py` 能單獨跑完整選股流程並推播 Telegram（依賴指標＋評分完成）
- [ ] GitHub Actions workflow 骨架：建 `.github/workflows/weekly_scan.yml`

  ```yaml
  name: 每週選股掃描
  on:
    schedule:
      - cron: '0 6 * * 5'   # UTC 06:00 = 台灣時間週五 14:00（收盤後）
    workflow_dispatch:        # 也可手動觸發
  jobs:
    scan:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v3
        - run: uv sync
        - run: uv run python main.py
          env:
            FINMIND_TOKEN: ${{ secrets.FINMIND_TOKEN }}
            TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
            TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  ```

- [ ] GitHub repo Settings → Secrets → Actions 新增：`FINMIND_TOKEN`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`
- [ ] `backend/alerts/scheduler.py`（Phase 6 建立時）定位為本機測試用，正式排程走 GitHub Actions
- [ ] GitHub Actions 手動觸發驗收（依賴 `main.py` 完整流程）

## 稽核發現（2026-07-29 全 repo 稽核）

三條「假資料看起來像真的」與其餘 11 項全部處理完畢，最終狀態見 PROJECT.md。
唯一保留為待辦的是需要新資料源的那條：

- [ ] 找櫃買指數的替代資料源（TPEx OpenAPI）——yfinance `^TWOII` 已失效（實測 `^TWOII`/`^TWO`/`^TPEX` 全回 0 筆），目前中台回 `null`、UI 誠實顯示「—」

## 待隊友回測 branch merge（合回 main 時逐項核對）

> 2026-09-22 盤點：remote 上沒有隊友的 branch（只有 `dashboard-ui`、`cache-persistence`、`watchlist-live-refresh` 三條都是自己的），回測進度不明——先問一下她推到哪裡了。

- [ ] 核對她的 branch 與 `backend/` 的指標/評分/優化模組**沒有重複實作**——有重疊先商量再 merge，不要兩份並存
- [ ] 回測模組接入選股流程（輸入輸出合約對齊；回測結果必含交易成本，費率見 docs/taiwan-market-notes.md）

## 刻意不做（避免範圍無限擴大）

看盤平台常見但暫不跟進：同類股/概念股比較、注意股/處置股清單、社群討論/多空投票、警示燈號標記。
