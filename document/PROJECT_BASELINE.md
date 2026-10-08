# Base Dashboard v0.1：專案基線

Base Dashboard 是可重用的網頁儀表板基礎專案。使用者以 JSON 指定組件與預設布局，在畫面中調整面板，並保存版面。它是獨立專案；目前示意資料不代表已串接 OlitGlobal 的模型庫、Object 或設備。

## 已完成範圍

| 項目 | v0.1 行為 |
|---|---|
| 執行方式 | Python 3.11+、FastAPI、Uvicorn |
| 前端 | 原生 HTML/CSS/JavaScript、GridStack 10.3.1 |
| 前端資源 | GridStack JS/CSS 隨專案保存，不需要 npm 或前端建置 |
| 組件來源 | data/components.json，可在介面匯入與匯出 |
| 面板操作 | 拖曳、縮放、新增、移除、鎖定 |
| 全螢幕 | 單一組件或整頁；若瀏覽器拒絕，組件改以網頁範圍放大 |
| 獨立頁面 | /widget/{component_id}，由同一組件配置重新建立內容 |
| 分離視窗 | 組件按鈕；主畫面保留占位，支援收回及關窗返回 |
| 保存布局 | data/layout.json，透過 API 保存與還原 |
| 自動驗證 | GitHub Actions：API 與 Chromium 操作測試 |

## 檔案與職責

| 路徑 | 職責 |
|---|---|
| main.py | FastAPI 路由、Pydantic 格式驗證、JSON 檔案存取 |
| static/index.html | 儀表板與獨立組件頁面的共用頁面 |
| static/dashboard.js | 組件繪製、GridStack 操作、全螢幕與分離視窗 |
| static/dashboard.css | 外觀、面板與全螢幕布局 |
| static/vendor/gridstack/ | 固定版本的第三方資源及授權文字 |
| data/components.json | 目前組件定義與預設布局，納入 Git |
| data/layout.json | 使用者保存的布局，不納入 Git |
| dashboard.example.json | 可匯入的範例配置 |
| document/dashboard.schema.json | 從後端模型產生的 JSON Schema |
| tests/ | 使用暫存資料的 API 與瀏覽器測試 |
| .github/workflows/tests.yml | 更新 main、PR 或手動觸發時執行驗證 |

## 資料流程

啟動頁面讀取 GET /api/components，繪製 JSON 的 widgets 預設布局。保存版面執行 PUT /api/layout；還原版面執行 GET /api/layout。開啟或重新整理頁面時會自動嘗試還原保存布局；尚未保存時使用 JSON 預設布局。保存布局損壞或引用已移除組件時，顯示原因並回到 JSON 預設布局，保留原保存檔供使用者處理。

匯入 JSON 執行 PUT /api/components，驗證通過後覆寫配置檔並重建主畫面。若舊布局引用了已刪除的組件，還原 API 回傳 409，提示使用者重設布局。

組件分離時使用 window.open 開啟獨立頁面。新頁面重新載入組件；透過 BroadcastChannel 通知主畫面返回，主畫面也會檢查子視窗是否關閉。

## 目前邊界

- 單人本機基線，所有瀏覽器共用配置與布局；尚未加入登入、多使用者隔離或多工作台。
- JSON 儲存配置及布局；目前數值卡、長條圖、清單與地圖均為示意，未加入即時資料訂閱。
- 分離視窗重新建立組件，不搬移既有 DOM，不保留任意內部互動狀態；iframe 會重新載入。
- 分離狀態不保存。刷新主頁時回到 Dashboard；重建布局時關閉子視窗。
- 瀏覽器決定開新視窗或分頁；已移除頁面內拖出區，不支援桌面程式式的跨視窗拖放。
- 網址驗收服務已於 2026-10-08 上線：https://base-dashboard-preview.onrender.com；Render Free，部署狀態 live，首頁、JSON API 和前端資源已確認 HTTP 200。

## 協作與驗證基線

使用者負責需求方向與成果驗收；開發方負責設計、實作、測試、除錯與 Git 同步。OK 表示確認並進入下一步；只有缺少必要外部資訊或關鍵方向需要決定時才停下詢問。

功能基線在提交 8f1ef6fe382023c49365c33a6a6036eb639a7099 通過 14 項測試：6 項 API、8 項 Chromium 操作測試。測試結果：https://github.com/benshen315/Base_Dashboard/actions/runs/37744377369 。

新增功能應補充其實際操作或資料一致性的測試；單純文件修改不另加測試。一般啟動方式及測試指令見根目錄 README.md。
