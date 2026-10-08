# 網址驗收部署

目標：使用者只開啟網址操作與驗收；開發方負責建置、部署、測試及除錯。

## 已上線的服務

| 設定 | 值 |
|---|---|
| 服務名稱 | base-dashboard-preview |
| 程式來源 | benshen315/Base_Dashboard，main 分支 |
| 執行環境 | Python 3.11，使用對應最新 patch |
| 計算方案 | Render Free web service |
| 地區 | Singapore |
| 安裝指令 | python -m pip install -r requirements.txt |
| 啟動指令 | python -m uvicorn main:app --host 0.0.0.0 --port $PORT |
| 健康檢查 | 平台根路徑檢查；額外驗證 GET /api/components |
| 自動部署 | 關閉；由開發方在確認測試通過後觸發部署 |

驗收網址：https://base-dashboard-preview.onrender.com

2026-10-08 已透過 Render 建立並部署，部署狀態為 live。服務 ID：srv-db3kv9ugekts73f7d8n0。部署程式版本：67bebde90c92f7d27146f43cd57c5ea1df5b2c67。首頁、JSON API 與前端 JavaScript 資源已確認 HTTP 200，近期 error 日誌為空。

根目錄 render.yaml 保存重建設定。本次由 MCP 直接建立服務，平台健康檢查使用根路徑；/api/components 另外以 HTTP 請求驗證。

## 執行與交付

帳號連接後，由開發方檢查已有服務，避免重複建立，再建立或更新 Python web service。等待建置與部署完成，檢查健康狀態、首頁、JSON 組件 API 及布局存取，最後提供服務實際回傳的 HTTPS 網址。

不得用預估的服務名稱組成網址當作已完成部署，也不得用 localhost 當作使用者可開啟的遠端驗收網址。

## 免費驗收環境的行為

Render Free 服務閒置約 15 分鐘會休眠，再次開啟可能等待約一分鐘。休眠、重啟或重新部署會清除本地檔案變更，所以匯入的組件及保存布局可能回到 Git 內的初始配置。

這是示範驗收環境；正式長期保存布局需要可持久保存的主機或儲存方案，再另行決定。此配置未建立付費服務、資料庫或磁碟。

目前應用沒有登入與使用者隔離。公開網址的訪客共用同一份示範配置與布局。

## 官方參考

- https://render.com/docs/deploy-fastapi
- https://render.com/docs/python-version
- https://render.com/docs/blueprint-spec
- https://render.com/docs/free
