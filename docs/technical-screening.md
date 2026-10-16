# 單股技術面篩選 v1

實作：`backend/screening/technical.py`。這是技術條件符合度，尚未經策略回測驗證，不是勝率，也沒有合併總體、基本面、籌碼或投組配置。

## 執行

根目錄先啟動中台，在另一個終端執行單股篩選：

```powershell
uv run uvicorn backend.data_service.main:app --port 8001
```

```powershell
uv run python -m backend.api.screen_stock 2330
uv run python -m backend.api.screen_stock 6488
```

可用 `DATA_SERVICE_URL` 指定中台；程式不直接向 Yahoo 抓資料。已建置並啟動 Docker Compose 時：

```bash
docker compose exec -T -w /app frontend python -m backend.api.screen_stock 2330
```

純計算可直接呼叫 `evaluate_technical(df, stale_adjust=False)`，輸入有開高低收量欄位、升冪且不重複的日 K `DatetimeIndex`，至少 60 根。呼叫端負責提供完整日 K。函式不改動輸入、不讀網路、不需要持倉。

CLI 固定向中台取一年日線。來源尚無可靠的收棒旗標，因此**一律排除台北日期的當日 K 棒，即使當天已收盤也一樣**，避免盤中使用未完成量價。輸出 `as_of` 是實際評分日，`excluded_current_day` 是移除根數；不會把舊一日數值冒充今日訊號。未來來源有可靠旗標時才開放當日收盤評分。

## 固定規則與權重

版本識別 `technical-v1`，沒有自動調參或自訂權重介面。

| 項目 | 得分條件 | 分數 | 必要 |
|---|---|---|---|
| 趨勢 | 收盤 > SMA20 > SMA60，等於不算 | 30 | 是 |
| MACD | MACD 線 > 0，或本根剛金叉 | 25 | 是 |
| 動能 | RSI14 在 40–70（含邊界），或 KD 本根金叉且 K < 80 | 25 | 是 |
| 量能 | 本根量／前 5 根均量 > 1.5；不含本根，等於 1.5 不算 | 15 | 是 |
| K 線型態 | 當根至少一個偏多型態 | 5 | 否 |

四個必要條件全部符合才 `passed:true`，無型態仍可通過（95 分）。型態只加一次 5 分，不以型態補足失敗的必要條件。這是單股技術過濾，沒有另發明「突破」事件；量能採規劃中必要的 1.5 倍條件，不能把放量本身當成突破。

MACD／KD 的金叉須「前根線值 ≤ 前根訊號線、當根線值 > 當根訊號線」，只判定本根，不把線持續在上方說成新交叉。型態重用 TA-Lib，但只對**當根**偏多結果加分，較早出現的不加。SMA／RSI／MACD／KD 的計算定義沿用共用指標，不改算法。

每項輸出 `id`、`passed`、`points`、`max_points`、`reason`、`values`，理由包含門檻與實際讀值。總分只加總各項得分；`scope:technical_only` 避免混淆為四層綜合評分。權重是首版研究設定，不代表已找出有效或最佳策略。

## 無法評分

| status | 說明 |
|---|---|
| `evaluated` | 完成計算，可讀取總分、通過狀態與五項理由 |
| `insufficient_data` | 少於 60 根、必要指標無有效值，或前 5 根均量為零 |
| `invalid_data` | 欄位缺漏、OHLCV 非有限／價格不合理、日期重複／亂序／非日 K，或 CLI 發現成交量時間不一致、未來日期 |
| `stale_adjustment` | 中台標記價格還原失敗，計算前停止 |
| `source_error` | 中台無資料、HTTP／連線失敗或無法解析 JSON |

後四種狀態 `score:null`、`passed:null`、`rules:[]`，附 `reason`；資料問題不冒充成 0 分或技術面不通過。成交量負數、零／負價格、缺值也不會被補成可評分數字。

## 驗證與範圍

全專案 55 項 pytest 通過；新增檢查包含真實指標串接、不修改輸入、分數加總、各必要門檻、RSI／量比／KD 邊界、交叉事件、舊型態不加分、異常資料及還原失敗停止計算。新增檔案 Ruff 檢查通過。

2026-10-16 使用真實中台與正式 Docker CLI，皆完成上市 2330、上櫃 6488 評分，當日排除一根，以 2026-10-15 為評分日，分別為 65／50 分、技術條件均未全部通過。這是當次資料驗收，不是固定預期分數或交易建議。Docker 測試使用獨立網路與暫存 SQLite，不修改現有預覽容器。

本次不新增 HTTP endpoint、不改個股 API 或 `/api/screening` 合約；整體選股頁仍是標示過的示範資料。批次掃描、頻率控制、持倉／賣出規則、ATR 停損、回測校準、基本面／籌碼與投組整合留待後續。
