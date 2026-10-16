# 目前架構

[開啟可互動架構圖](../.archify/architecture-tw-stock-quant-20261015-092658/tw-stock-quant.html)

圖檔保留 PR #6 目錄整理時的來源快照；本分支新增的指標模組與型態辨識，以以下目錄及程式為準。

```text
tw-stock-quant/
├── frontend/                 # Next.js 頁面、元件與 /api Route Handlers
│   └── src/
│       ├── app/
│       ├── components/      # 六層 K 線圖、指標說明與速查卡
│       └── lib/              # 中台 client、Python 子程序、指標判讀與合約型別
├── backend/                  # Python 程式，與前端共用根目錄的 uv 環境
│   ├── api/get_stock_data.py # 原有個股計算與前端 JSON 組裝
│   ├── data/universe.py     # 本機一般股票清單與上市／上櫃代碼解析
│   ├── api/screen_stock.py # 單股日 K 技術篩選 CLI，中台唯一行情來源
│   ├── screening/technical.py # 純規則、符合度分數與解釋
│   ├── indicators/           # 共用數值指標與 TA-Lib K 線型態
│   └── data_service/         # FastAPI raw 資料 API
│       ├── main.py
│       ├── sources/          # yfinance／twstock
│       ├── cache.py          # 記憶體 TTL
│       └── store.py          # SQLite 歷史 K 線
├── data/                     # 執行期資料，data/cache.db 保留既有位置
├── tests/                    # 指標數值、離線合約、品質阻擋與資料位置驗證
├── scripts/                  # 本機啟動及部署 smoke check
├── docs/                     # 架構、操作及台股筆記
├── .archify/                 # 架構圖 JSON、HTML 與自動驗證收據
├── .github/workflows/        # CI 與 self-hosted runner 部署
├── Dockerfile
├── docker-compose.yaml
└── pyproject.toml / uv.lock
```

瀏覽器向 Next.js 的 `/api` 請求資料。部分 Route Handler 直接代理中台 HTTP API，
個股 K 線則由 `run-python.ts` 在前端容器啟動 `backend/api/get_stock_data.py`，
以 `python -m backend.api.get_stock_data` 向中台要 raw candles，使用
`backend.indicators.add_indicators` 計算指標，再透過 stdout 回傳 JSON。
型態辨識使用 TA-Lib，只回最近 5 根 K 棒的訊號；回測功能尚未接入。

個股 JSON 包含 `sma20`／`sma60`、`rsi`、`macd`、`kd.k`／`kd.d`、`atr14`、均量與型態。
`frontend/src/lib/indicator-summary.ts` 判讀當根有效數值，`indicator-help.tsx` 提供可展開說明；
圖表六個 pane 依序是 K 線與 SMA、成交量、RSI、MACD、KD、ATR。速查與圖表使用相同計算序列，
速查缺值顯示 —；MACD 線位置不當成交叉事件。

中台若回 `stale_adjust:true`，個股 wrapper 在計算前停止，只回錯誤與旗標。
Next Route Handler 對此回 503，個股頁清除舊資料並顯示原因，定期更新成功後恢復。
成功回應帶 `stale_adjust:false`。中台 raw HTTP contract 沒有變更，擴充的是個股前端合約。
計算與平台算法差異、測試範圍見 [指標驗證](indicator-review.md)。

中台是唯一抓取外部市場資料的服務。記憶體 TTL 減少重複抓取；歷史日／週／月 K 線
由 `store.py` 寫入 `data/cache.db`，Docker 掛載 `stock-data` volume 保存。
PR #6 的目錄搬移沒有更改資料檔位置、API contract、服務 port 或容器名稱；
後續指標擴充由 PR #7 同步調整 Python 輸出與前端型別。

`backend.data.universe` 只讀本機 twstock 表，不抓行情；搜尋與未來批次掃描共用它的一般股票清單。
中台 K 線、前收盤、基本面及分時共用市場解析，上市用 `.TW`、上櫃用 `.TWO`；
SQLite 鍵也使用完整代碼，兩市場不混用。端點及成功 JSON 形狀不變，未知代碼在網路抓取前回 404。
這項擴充尚未包含批次掃描、頻率控制或真實全市場排行榜。

單股技術篩選透過 `backend.api.screen_stock` 向中台取一年日 K，先排除當日，
再交給純計算的 `backend.screening.technical.evaluate_technical` 重用指標層。
結果包含 technical-v1 分數、必要門檻與各項理由；品質／來源問題回 null 分數，不冒充低分。
目前僅 Python／CLI 使用，不新增 HTTP endpoint，亦不替換 `/api/screening` 的多因子示範合約。
詳細資料流邊界與限制見 [技術篩選](technical-screening.md)。
自選股保存在瀏覽器 localStorage；部分籌碼、新聞、排行榜、選股資料仍是畫面有標記的示範資料。

Docker image 同時包含 Node 與 Python，分成前端及中台兩個服務。對外僅發布前端
`BIND_ADDRESS:PORT`（預設 `127.0.0.1:3000`），中台透過 Compose 內網的
`http://data-service:8001` 存取。服務內部模組路徑為 `backend.data_service.main:app`。
CI 通過後由 `tw-stock` runner 部署；操作步驟見 [MAINTAINERS.md](MAINTAINERS.md)。

架構圖由專案內 Archify 3.1.0 產生，綁定本機已提交的來源版本。圖中的來源路徑
可供查核；未推送的 commit 不會假裝是 GitHub 上已部署的版本。
