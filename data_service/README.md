# 資料中台（data_service）

負責向外部來源（yfinance、twstock）抓取 + 記憶體 TTL 快取資料，前端與後端都跟這裡要資料，
不要自己重打外部 API。完整背景見 [../docs/thinking.md](../docs/thinking.md) 2026-07-01「拆出資料中台」。

## 啟動

```bash
uv run uvicorn data_service.main:app --reload --port 8001
```

啟動後可以直接開 http://localhost:8001/docs 看互動式 API 文件（FastAPI 自動產生）。

## Endpoints

| Method | Path | 說明 | TTL |
|---|---|---|---|
| GET | `/health` | 存活檢查 | — |
| GET | `/stocks/{ticker}/candles?period=&interval=` | raw OHLCV + 成交量 + 漲跌停價（不含技術指標） | 60s |
| GET | `/stocks/{ticker}/profile` | 產業別/上市櫃別/本益比/股價淨值比/殖利率/EPS/52週高低/市值/股本/分析師目標價 | 1800s |
| GET | `/stocks/{ticker}/orderbook` | 五檔委買委賣 | 30s |
| GET | `/stocks/{ticker}/intraday` | 今日 1 分鐘分時走勢 | 30s |
| GET | `/market/indices` | 加權指數/櫃買指數/道瓊/那斯達克/日經/上證 | 30s |
| GET | `/market/intraday` | 加權指數今日 1 分鐘分時走勢 | 30s |

`period`/`interval` 是 yfinance 的字串格式，例如 `period=6mo&interval=1d`、`period=1d&interval=5m`。

## 給後端（計算層）的邊界

中台**只做抓取 + 快取**，不算任何技術指標或評分。SMA/RSI/MACD、K 線型態辨識、選股評分、
投組優化這些「計算」都是後端的工作——跟中台要 raw candles，自己算完再回傳給前端。

錯誤一律回傳標準 HTTP 狀態碼（例如查無資料是 404 + `{"detail": "..."}`），不是 200 + `{"error": ...}`。

## 快取

記憶體 TTL cache（`cache.py`），依資料更新頻率分三個等級：近即時資料（五檔/分時/大盤指數）30s、
K 線 60s、基本面 1800s。重啟服務會清空快取、多個服務實例之間不共享——目前先接受這個限制，
之後有需要再換 Redis/SQLite。
