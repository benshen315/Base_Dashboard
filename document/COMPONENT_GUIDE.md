# JSON 組件與擴充方式

配置分成 components 和 widgets：前者定義組件，後者定義面板實例。同一組件可以建立多個面板實例，實例各自保存位置與大小。

## 完整最小配置

```json
{
  "schema_version": 1,
  "title": "我的工作台",
  "components": [
    {
      "id": "temperature",
      "title": "溫度",
      "type": "metric",
      "data": {
        "value": 26.5,
        "unit": "°C",
        "description": "範例資料"
      },
      "fullscreen": true,
      "popout": true
    }
  ],
  "widgets": [
    {
      "id": "temperature-card-1",
      "component": "temperature",
      "x": 0,
      "y": 0,
      "w": 4,
      "h": 3
    }
  ]
}
```

## 組件欄位

| 欄位 | 用途及限制 |
|---|---|
| id | 組件唯一識別；1–100 字元，只使用英數、底線或連字號 |
| title | 顯示名稱，1–200 字元 |
| type | metric、text、list、bar、map 或 iframe |
| data | 組件資料物件；不同 type 使用下表欄位 |
| fullscreen | 是否顯示組件全螢幕按鈕，預設 true |
| popout | 是否允許組件分離至新視窗，預設 true |

fullscreen/popout 是介面功能開關，不是存取權限設定。

| type | data 範例 | 說明 |
|---|---|---|
| metric | {"value":128,"unit":"個","description":"模型數量"} | 數值卡 |
| text | {"text":"工作備註"} | 純文字，支援換行 |
| list | {"items":[{"label":"P01","value":"正常"}]} | label/value 清單 |
| bar | {"values":[10,30],"labels":["一","二"]} | 非負數長條；依最大值縮放高度 |
| map | {"caption":"示意地圖"} | 目前為固定地圖示意圖 |
| iframe | {"url":"/viewer"} | 嵌入已有頁面；/viewer 是範例路徑，專案未實作此路由 |

data 以 JSON 物件接收；後端依 type 驗證清單項目、有限數字、文字欄位與 iframe URL。格式不符時拒絕匯入並保留原配置。未提供的可選欄位維持前端預設顯示；長條圖的負值仍按 0 顯示。JSON Schema 描述後端模型欄位；組件 data 的詳細限制、唯一性、組件引用及 x+w 邊界由後端額外檢查。

## 面板欄位

| 欄位 | 限制 |
|---|---|
| id | 面板實例唯一 ID；格式與組件 id 相同 |
| component | 必須引用 components 中存在的 id |
| x | 0–11，從左側開始計算 |
| y | 0–10000，從上方開始計算 |
| w | 1–12 欄，且 x+w 不可超過 12 |
| h | 1–100 格；目前每格高度為 88 px |

components 可有 1–100 個定義，widgets 可有 0–100 個實例。空 widgets 表示空工作台，仍可從清單加入組件。

## 加入組件的三種方式

1. 使用已有 type：在 components 中新增定義，在 widgets 中加入實例，或透過介面選擇後新增。不需要修改程式。
2. 嵌入既有工具：使用 iframe，提供實際已存在的 URL。目標頁面需允許被嵌入；配置不會替你建立服務、處理認證或解除網站的嵌入限制。
3. 新增繪製類型：在 main.py 的 Component.type 加入類型，在 dashboard.js 的 drawBody 中實作 renderer。共用 panel 已提供標題列、全螢幕及分離視窗，新 renderer 只需繪製內容。新增類型需補上資料驗證及相關操作測試。

## 接入真實資料

目前 type 與 data 定義顯示內容，尚未定義 API URL、更新頻率或即時訂閱欄位。接入新資料來源時，由後端提供資料 API，再讓 renderer 讀取及更新；不在 JSON 內放入可執行 JavaScript。

對 Three.js 或 Cesium 等 Viewer，容器大小改變時需更新渲染尺寸。獨立視窗是另一個頁面與執行實例，若要延續相機位置、選取或其他狀態，需另設可序列化的狀態交換，v0.1 尚未提供。

## MENU 上傳與註冊

開啟「MENU · 組件管理」，下載範例或上傳 JSON。可上傳單一組件物件，或 `{ "components": [...] }` 批次組件。確認註冊後追加至組件清單，不覆寫原組件或目前版面。相同 ID、無效資料或超過 100 個組件會拒絕整批註冊；修正 ID 後可重試。註冊完成後按「加入工作台」，再保存版面。

API：POST /api/components/register，JSON body 為 `{ "components": [...] }`；成功回傳 201 及完整配置。此功能註冊既有 metric、text、list、bar、map、iframe 類型的 JSON 組件。獨立視窗由組件按鈕開啟，已移除拖出提示區。
