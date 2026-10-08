# Base Dashboard v0.1

可重用的儀表板基礎專案，採 FastAPI + 原生 HTML/CSS/JavaScript + GridStack。

Python 3.11+，無需 Node.js / npm。GridStack 10.3.1 隨專案存放於 static/vendor/gridstack，啟動後無需連網載入 CDN。第三方授權文字保留在該目錄。

## 專案文件

- [專案基線與目前邊界](document/PROJECT_BASELINE.md)
- [JSON 組件格式與擴充方式](document/COMPONENT_GUIDE.md)
- [後端模型 JSON Schema](document/dashboard.schema.json)

## 啟動

在本目錄開啟終端機：

```bash
python -m venv .venv
```

Windows PowerShell 啟用：`.venv\Scripts\Activate.ps1`

Ubuntu 啟用：`source .venv/bin/activate`

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

開啟 http://127.0.0.1:8000 ，API 文件：http://127.0.0.1:8000/docs 。

PyCharm：工作目錄設為本專案目錄，Module name：`uvicorn`，Parameters：`main:app --reload --host 127.0.0.1 --port 8000`。

## JSON 組件

啟動時從 `data/components.json` 載入組件清單和預設布局。可直接修改該檔後重新整理頁面，或在介面按「匯入 JSON 檔」；後者經 FastAPI 驗證後覆寫 components.json。`dashboard.example.json` 為完整範例。

`components` 定義組件，`widgets` 定義面板實例及位置。同一個組件可以加入多個實例，實例 ID 必須唯一。以下是可匯入的最小範例：

```json
{
  "schema_version": 1,
  "title": "我的 Dashboard",
  "components": [
    {
      "id": "models",
      "title": "模型數量",
      "type": "metric",
      "data": {"value": 128, "unit": "個模型", "description": "示意資料"},
      "fullscreen": true,
      "popout": true
    }
  ],
  "widgets": [
    {"id": "models-1", "component": "models", "x": 0, "y": 0, "w": 4, "h": 3}
  ]
}
```

支援的 type：

| type | data 欄位 | 用途 |
|---|---|---|
| metric | value, unit, description | 數值卡 |
| text | text | 備註文字 |
| list | items: [{label, value}] | 資料清單 |
| bar | values: [數字], labels: [文字] | 長條圖 |
| map | caption | 靜態示意地圖 |
| iframe | url | 嵌入既有網頁，如 `/viewer` 或 `https://...` |

JSON 提供組件資料及配置，不執行任意 HTML/JavaScript。新增 type 時需在 dashboard.js 加入 renderer，並更新後端允許的 type。iframe 的目標網站必須允許被嵌入；Demo 沒有包含真實 Three.js / Cesium Viewer。

## 操作

- 拖曳標題列調整位置；右下角調整大小。
- 下拉選擇組件後按「加入組件」，× 可移除實例。
- 「保存版面」透過 PUT /api/layout 寫入 data/layout.json；開啟或刷新主頁時自動還原，也可按「還原版面」手動載入。尚未保存時使用 JSON 預設布局；保存布局失效時提示原因並回到預設布局。
- 「預設版面」回到 components.json 的 widgets，不直接覆寫已保存版面。
- 「下載組件 JSON」匯出目前組件定義和畫面布局，可再次匯入。
- 「全螢幕」將單一組件切換至瀏覽器 Fullscreen API，Esc 退出；若 API 不可用，則放大至網頁範圍。
- 「整頁全螢幕」切換整個 Dashboard。
- 「獨立視窗」開啟 /widget/{component_id}，主畫面保留占位面板。關閉新視窗、按「收回組件」，或在新視窗按「返回工作台」即可返回。
- 拖曳標題列到頁面下方的「獨立視窗區」也會開啟獨立組件網頁。若瀏覽器阻擋，頁面會顯示按鈕供再次開啟。

瀏覽器不能可靠追蹤面板被拖出網頁邊界後的滑鼠放開事件，因此採用頁面內拖出區。新視窗或分頁由瀏覽器設定決定，可手動移到其他螢幕；不是桌面程式式的原生跨視窗拖放。

獨立視窗重新從伺服器載入同一組件定義，沒有搬移既有 DOM，也沒有同步任意互動狀態。iframe 內容會重新載入。獨立视窗狀態不寫入布局檔；刷新主頁時組件回到 Dashboard。匯入或重新載入布局時，已分離的子視窗會關閉。

## API

- GET /api/components：讀取完整 JSON 配置。
- PUT /api/components：驗證並保存 JSON 配置。
- GET /api/layout、PUT /api/layout：保存與讀取布局。
- GET /widget/{component_id}：獨立組件網頁。

所有內容均為示意。本機單人 Demo，所有瀏覽器共用一份配置與版面，未加入登入和使用者隔離。

## 自動驗證

開發測試額外依賴（一般啟動不需要）：

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install --with-deps chromium
python -m pytest tests -q --browser chromium
```

GitHub Actions 會在 main 更新及 Pull Request 執行 API 和 Chromium 操作測試。失敗時保存截圖及 trace，供除錯。測試使用暫存資料目錄，不會改動正式 components.json 或 layout.json。

可透過 BASE_DASHBOARD_DATA_DIR 指定配置與版面檔的儲存目錄；該目錄需先放入 components.json。未設定時維持使用專案 data/。
