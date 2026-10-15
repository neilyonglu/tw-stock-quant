# 指標完成度與數值驗證

檢查日期：2026-10-15。範圍為 `feature/indicators-module` 的計算、個股 API、頁面與價格品質處理。

變更見 [PR #7](https://github.com/neilyonglu/tw-stock-quant/pull/7)；本機 3107 預覽與手動檢查位置見 [操作文件](MAINTAINERS.md#本機預覽與重新建置)。推送分支不會更新 server，須合併 main 並通過部署流程。

**指標串接與說明已完成，算法參考對照通過。未取得同批券商匯出行情，因此沒有宣稱逐筆對齊券商實際畫面的數值。**

| 指標 | 計算與頁面 | 規則 |
|---|---|---|
| SMA20／60 | 圖表、速查、說明 | 依所選 K 棒週期 |
| EMA | 可重用計算、MACD 內部使用 | 首價起算，權重 2/(n+1) |
| RSI14 | 圖表、速查、說明 | Wilder 平滑；需 15 根 |
| MACD12／26／9 | 線、訊號線、柱狀圖、速查、說明 | 收盤價來源，柱狀圖為兩線差，不乘 2 |
| KD9／3／3 | K／D 副圖、速查、說明 | 遞迴平滑，初始 50；需 9 根 |
| ATR14 | 副圖、速查、說明 | Wilder 平滑；需 15 根；單位元 |
| 5／10 期均量 | 圖表、速查、說明 | 包含本根 |
| 量比 | 速查、訊號、說明 | 本根量／前 5 根均量，不含本根 |
| K 線型態 | TA-Lib 辨識、訊號、說明 | 最近 5 根，不保證反轉 |

## 價格品質與合約

中台介面保持不變，前端 `StockData` 與 Python 輸出同步新增 `kd`、`atr14` 及成功回應的 `stale_adjust:false`。

中台回 `stale_adjust:true` 時，Python 在計算前停止，只輸出錯誤與旗標。Next API 回 503，不附舊價格或指標。個股頁清除先前資料並顯示價格還原失敗，依現有自動更新機制重試，恢復後自動顯示資料；自選股遇非成功回應也不顯示這筆舊報價。

圖表與速查共用同批計算結果。資料不足、非有限或時間戳不是當根時，速查顯示 —。相容性欄位 `latest.rsi` 與 `latest.macd_crossover` 保留，但頁面不使用它們判讀；SMA／MACD 描述位置，不誤稱交叉事件。

## 數值驗證

使用 `tests/indicators/conftest.py` 固定 seed=42 的 300 根 OHLCV。可執行 `uv run --no-sync pytest -q` 重跑，資料與實際市場來源無關。

| TA-Lib 對照 | 比對範圍 | 最大絕對誤差 |
|---|---|---|
| SMA20 | 全部有效值 | 7.11e-14 |
| RSI14 | 全部有效值 | 1.42e-14 |
| ATR14 | 全部有效值 | 0 |
| EMA12 | 最後 50 根 | 1.42e-14 |
| MACD 線 | 最後 50 根 | 7.74e-9 |
| 訊號線 | 最後 50 根 | 1.14e-8 |
| 柱狀圖 | 最後 50 根 | 3.64e-9 |

MACD 全序列另通過獨立逐根 EMA 遞迴公式比對，KD 全部有效值通過補 50 種子的獨立指數平滑參考比對，容許絕對誤差 1e-10。手算案例 RSV 從 50 到 100 後，K=66.6667、D=55.5556。

## 券商／TradingView 差異

- [TradingView RSI](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/) 使用漲跌幅的 RMA。本專案採 Wilder 版本，有效區間與 TA-Lib 吻合；完全平盤可能無定義，頁面顯示 —。
- [TradingView EMA](https://www.tradingview.com/support/solutions/43000592270-exponential-moving-average/) 與 [MACD](https://www.tradingview.com/support/solutions/43000502344-moving-average-convergence-divergence-macd-indicator/) 的遞迴／線差公式已核對。本專案 EMA 首價起算，TA-Lib 採 SMA 種子，短歷史及早期數值不保證一致。
- [TradingView ATR](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/) 預設使用 TR 的 RMA。本專案採 TA-Lib 的第 1–14 個具前收盤 TR 作種子；平台首根處理若不同，短區間仍可能不同。
- [元大 KD 說明](https://jdata.yuanta.com.tw/z/zk/zkstudy.htm) 列出初始 50、權重 1/3 與常用 9 期。[TradingView STOCH](https://www.tradingview.com/support/solutions/43000502332-stochastic-stoch/) 則使用 SMA 平滑，預設回看期數也不同。固定資料末根本專案 K/D=25.5436/30.6881；同樣 9/3/3 的 SMA STOCH 為 22.5505/26.9437，差異來自算法，並非增加歷史就能消除。

以上核對公開公式與設定；表中數字來自本機參考計算，沒有使用未取得的券商畫面數字。要對齊指定券商，仍須相同 OHLCV、還原方式、起始時間、週期、價格來源與參數；不能承諾各平台預設值一致。

## 驗證與邊界

- 23 個 Python 測試：數值、KD／ATR JSON、空輸入、還原失敗不呼叫計算。
- 原生 Node 檢查與正式 Docker image 內離線檢查通過。
- 正式前端、Docker image 建置通過。
- 實際 Next Route → Python → 本機測試中台驗證成功序列與 stale 503，使用測試資料。
- Chrome 1440px／375px：KD／ATR、六層圖表、鍵盤說明、44px 操作區、無水平溢出、短資料 —、背景更新失敗隱藏資料及恢復皆通過。

本分支不增加獨立 EMA 圖線、交叉通知、交易策略或選股評分。上櫃 `.TWO` 支援仍屬資料管線待辦；指標計算完成不代表策略獲利能力已驗證。
