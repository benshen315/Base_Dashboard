# OlitGlobal Web OS v0.2 驗收

Vue 3、PrimeVue 4 Aura、Tailwind CSS 4、Vite 6、Pinia 3、interact.js、ECharts 5；FastAPI 保留既有組件 API 並新增刪除及健康 API。

## 入口與操作

- `/` 新版桌面；`/legacy` 原有 GridStack 儀表板；`/widget/{id}` 原有獨立組件頁；`/api/health` 服務版本。
- 點按 APP 開啟；搜尋依名稱篩選。
- 右鍵、Shift+F10 或觸控長按 550ms 使用同一 PrimeVue ContextMenu。移動超過 10px 或放開取消長按。
- APP 選單提供開啟、電腦開啟新視窗及管理；空白桌面選單提供顯示桌面、設定及重新載入。底部 Dock 已依需求移除。
- 拖曳標題列移動；拖曳左右、下緣縮放。支援置頂、最小化、還原、最大化、關閉。點按左上品牌返回桌面，點 APP 圖標還原其視窗。
- 640px 以下使用 iPhone 模式：一次顯示一個滿版 APP、返回主畫面、最近 APP 切換及結束 APP；APP 內不顯示桌面視窗控制或 Dock。641px 以上使用電腦多視窗模式。調整瀏覽器寬度時自動切換，保留已開啟 APP。
- 組件管理可註冊／上傳 JSON、改名、匯出、刪除。後端拒絕重複 ID、無效資料及刪除最後一個組件。
- 壁紙保存在目前瀏覽器。視窗狀態不保存。

## 建置與驗證

Python 3.11+、Node 24、pnpm 11.25.0。

```sh
python -m pip install -r requirements-dev.txt
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend test
pnpm --dir frontend build
python -m playwright install chromium
python -m pytest tests -q --browser chromium
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

前端原始碼位於 frontend，建置結果 static/os 隨 Git 提交，現有 Python Render 建置命令不需變更，執行時不依賴 CDN。GitHub Actions 重新建置並執行前後端與瀏覽器測試。

開發：啟動 API 後執行 `pnpm --dir frontend dev`，開啟 Vite 的 `/os/` URL。

## 第一版邊界

單人驗收服務，沒有登入與使用者隔離；配置修改為服務共用。圖表、數值及地圖均為示意，未連接 OlitGlobal 實際模型、Object 或設備。地圖可註冊 iframe 替換 viewer；能否嵌入取決於外部網站政策。

Render Free 的 JSON 修改只存在目前執行個體，重啟或部署可能回復 Git 配置；正式持久化需資料庫或持久儲存。刪除後原有保存布局若仍引用該組件，既有 API 回傳 409，需在舊儀表板重設布局。

Registry、組件 renderer、Pinia Window Manager 與系統 APP 分離；JSON 註冊不執行任意程式碼。新增可執行的系統 APP 需修改程式。
