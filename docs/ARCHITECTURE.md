# 目前架構

[開啟可互動架構圖](../.archify/architecture-tw-stock-quant-20261015-092658/tw-stock-quant.html)

```text
tw-stock-quant/
├── frontend/                 # Next.js 頁面、元件與 /api Route Handlers
│   └── src/
│       ├── app/
│       ├── components/
│       └── lib/              # 中台 HTTP client、Python 子程序、型別與示範資料
├── backend/                  # Python 程式，與前端共用根目錄的 uv 環境
│   ├── api/get_stock_data.py # 原有個股計算與前端 JSON 組裝
│   └── data_service/         # FastAPI raw 資料 API
│       ├── main.py
│       ├── sources/          # yfinance／twstock
│       ├── cache.py          # 記憶體 TTL
│       └── store.py          # SQLite 歷史 K 線
├── data/                     # 執行期資料，data/cache.db 保留既有位置
├── tests/                    # 離線合約、套件匯入與資料位置驗證
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
向中台要 raw candles 後計算 SMA／RSI／MACD，再透過 stdout 回傳 JSON。
Python 計算層目前仍是原有腳本；沒有帶入其他分支的指標模組或回測功能。

中台是唯一抓取外部市場資料的服務。記憶體 TTL 減少重複抓取；歷史日／週／月 K 線
由 `store.py` 寫入 `data/cache.db`，Docker 掛載 `stock-data` volume 保存。
目錄搬移沒有更改資料檔位置、API contract、服務 port 或容器名稱。
自選股保存在瀏覽器 localStorage；部分籌碼、新聞、排行榜、選股資料仍是畫面有標記的示範資料。

Docker image 同時包含 Node 與 Python，分成前端及中台兩個服務。對外僅發布前端
`BIND_ADDRESS:PORT`（預設 `127.0.0.1:3000`），中台透過 Compose 內網的
`http://data-service:8001` 存取。服務內部模組路徑為 `backend.data_service.main:app`。
CI 通過後由 `tw-stock` runner 部署；操作步驟見 [MAINTAINERS.md](MAINTAINERS.md)。

架構圖由專案內 Archify 3.1.0 產生，綁定本機已提交的來源版本。圖中的來源路徑
可供查核；未推送的 commit 不會假裝是 GitHub 上已部署的版本。
