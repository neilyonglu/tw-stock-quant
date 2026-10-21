# CI 與 server 部署

GitHub 雲端 CI 用 `pytest -q` 執行完整離線測試，涵蓋指標、個股 JSON、上市櫃來源、快取及單股技術與基本面研究，再跑 production image build、image 內離線 Node 指標判讀檢查、容器健康檢查及前端到中台的搜尋請求。
搜尋使用 twstock 本機代碼表，不把外部行情來源的暫時失敗當成 CI 失敗。
所有 push 都跑 CI；只有 main 的 CI 成功後會自動部署。PR 不會使用正式 server runner。

| 項目 | 設定 |
|---|---|
| Runner 名稱 | 使用者註冊的 `genton-server` |
| Runner 標籤 | `self-hosted`、`Linux`、`X64`、`tw-stock` |
| 部署 clone | `/mnt/ssd/self-proj/tw-stock-quant` |
| 建議 runner 目錄 | `/mnt/ssd/self-proj/actions-runners/tw-stock-quant` |
| Compose project | `tw-stock-quant`（固定，沿用 volume） |

## 本機預覽與重新建置

在專案根目錄的 PowerShell 執行以下指令，以 3107 避開 Forge 等服務的 3000：

```powershell
$env:PORT = "3107"
docker compose -p tw-stock-quant up -d --build --wait
docker compose -p tw-stock-quant ps
```

開啟 http://localhost:3107/stock/2330 。修改程式或拉取新版本後，也使用同一條 `up --build` 指令；只重新整理瀏覽器不會更新 image。

`PORT` 控制宿主機映射，容器內仍是 3000，中台仍是 Compose 內網的 8001。PowerShell 的設定只影響目前視窗與子程序，不會修改 server。若要固定本機設定，可在未追蹤的根目錄 `.env` 加入 `PORT=3107`，保留其他既有設定；同名 shell 環境變數優先於 `.env`。

手動檢查以下位置：

1. 「K 線圖」展開「圖表指標怎麼看」；副圖由上至下為成交量、RSI、MACD、KD、ATR。
2. 「速查指標」查看 KD(9,3,3)、ATR(14) 卡片，點指標名稱旁 ⓘ 展開說明。
3. 切換週期確認每根 K 棒時間提示，資料不足時顯示 —。今日分鐘線是否不足取決於當時實際資料根數。
4. 控制欄看不到捲軸，仍能滾動至五檔報價。

`stale_adjust` 是異常狀態，不需刻意改正式資料觸發；已有離線及本機測試中台驗證 503、舊資料隱藏與後續恢復。數值對照及限制見 [indicator-review.md](indicator-review.md)。

離線檢查可在根目錄執行：

```powershell
uv sync --locked --no-default-groups --group dev
uv run --no-sync pytest -q
docker run --rm --network none --mount "type=bind,src=$PWD/frontend,dst=/checks,readonly" tw-stock-quant:latest node --experimental-strip-types /checks/scripts/check-indicators.mjs
```

最後一條使用剛建置的專案 image 和唯讀原始碼，無需額外安裝 Node 測試框架。

單股技術面篩選需運行中的中台，可執行 `uv run python -m backend.api.screen_stock 2330`，
或 `docker compose exec -T -w /app frontend python -m backend.api.screen_stock 2330`。
此功能尚未接到選股頁；JSON 分數為規則符合度，CLI 一律排除當日 K，需檢查 `as_of`。
完整規則與狀態見 [technical-screening.md](technical-screening.md)。

## Server 首次設定

使用能操作 Docker 的 genton 帳號，將 repo clone 到部署目錄；runner 安裝目錄與 clone 分開。
如果 repo 是 private，沿用 server 的 Git 驗證方式或設定唯讀 deploy key。

```bash
mkdir -p /mnt/ssd/self-proj
git clone https://github.com/neilyonglu/tw-stock-quant.git /mnt/ssd/self-proj/tw-stock-quant
cd /mnt/ssd/self-proj/tw-stock-quant
git switch main
git fetch origin main
docker info >/dev/null
docker compose version
```

GitHub repo 的 Settings → Actions → Runners 確認本專案 runner 已註冊、標籤包含 `tw-stock`，
狀態為 Idle。新註冊時使用頁面產生的下載、驗證與 config 指令，加上
`--name genton-server --labels tw-stock`。Token 只在 server 使用。
在該 runner 安裝目錄啟動背景服務：

```bash
sudo ./svc.sh install "$(whoami)"
sudo ./svc.sh start
sudo ./svc.sh status
```

`.env` 可選，用來設定 PORT/BIND_ADDRESS；預設綁 `127.0.0.1:3000`。
同一台 server 上先確認 3000 未被其他服務使用。對外使用 HTTPS reverse proxy 或 SSH tunnel；
公開前先升級 Next.js 16.2.9，現有版本在 npm audit 有 critical 安全告警。

## 部署與驗收

feature branch push 只跑 CI；合併 main 後，CI 通過再交給 `tw-stock` runner。
部署 clone 必須在 main、已追蹤檔案沒有本機修改；workflow fast-forward 到 CI 通過的精確 SHA。
本機 main 超前或分岔時拒絕部署，不覆蓋本機修改或自動降版。
Server 上建置 image 成功後才替換容器；健康檢查失敗不會自動回滾。

```bash
cd /mnt/ssd/self-proj/tw-stock-quant
docker compose -p tw-stock-quant ps
docker compose -p tw-stock-quant logs --tail 100
docker compose -p tw-stock-quant exec -T frontend python - < scripts/check_deployment.py
```

最後一個檢查會抓上市 2330 與上櫃 6488 的搜尋、K 線／指標與基本面市場別，需兩市場來源都可達，只在需要驗證外部來源時手動跑。它不取代離線 CI，也不代表已掃描所有股票。

清單與市場解析可在根目錄離線驗證：

```bash
uv run python -m backend.data.universe
```

數量隨 twstock 代碼表快照變動；新掛牌查不到時先檢查代碼表，不要靠改後綴猜市場。上櫃來源支援不等於已補齊櫃買指數 `^TWOII`，後者仍是獨立資料來源待辦。
不要使用 `down -v`，它會刪除正式 SQLite volume。
可在 Actions → Test and deploy stock dashboard → Run workflow 選 main 手動重跑。
CI／部署是否可用以 GitHub 實際執行結果為準；workflow 推送成功不代表 server 已部署。
