# CI 與 server 部署

GitHub 雲端 CI 用 pytest 執行指標及個股 JSON 離線測試，再跑 production image build、容器健康檢查及前端到中台的搜尋請求。
搜尋使用 twstock 本機代碼表，不把外部行情來源的暫時失敗當成 CI 失敗。
所有 push 都跑 CI；只有 main 的 CI 成功後會自動部署。PR 不會使用正式 server runner。

| 項目 | 設定 |
|---|---|
| Runner 名稱 | 使用者註冊的 `genton-server` |
| Runner 標籤 | `self-hosted`、`Linux`、`X64`、`tw-stock` |
| 部署 clone | `/mnt/ssd/self-proj/tw-stock-quant` |
| 建議 runner 目錄 | `/mnt/ssd/self-proj/actions-runners/tw-stock-quant` |
| Compose project | `tw-stock-quant`（固定，沿用 volume） |

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

最後一個檢查會抓真實行情，只在需要驗證外部來源時手動跑。
不要使用 `down -v`，它會刪除正式 SQLite volume。
可在 Actions → Test and deploy stock dashboard → Run workflow 選 main 手動重跑。
CI／部署是否可用以 GitHub 實際執行結果為準；workflow 推送成功不代表 server 已部署。
