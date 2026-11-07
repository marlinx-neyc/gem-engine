# 🌊 GEM Engine UI/UX 儀表板架構與數據同化規範指南 (Dashboard Governance Standard)

> **版本**：v88.0 Flagship Standard  
> **核心原則**：`Layout Frozen, Data Fluid`（UI/UX 版面結構剛性凍結，僅允許後端數據層動態注入更新）

---

## 📌 1. 規範宗旨 (Purpose)
本規範確立「龜山島全域海事戰術指揮中樞」前端視覺面板的唯一標準結構。為了確保指揮官與現場營運人員在跨設備（手機/平版/桌面）下使用體驗一致，**後續所有演算法更新、模型優化或數據對算，均不得修改前端 DOM 結構與 CSS 佈局**，所有動態數值一律透過 `data/live_status.json` 與 `window.INITIAL_LIVE_DATA` 自動寫入與刷寫。

---

## 🏛️ 2. 面板組件結構規範 (UI Component Specifications)

### 2.1 頂部動態跑馬燈區塊 (Marquee Banner)
* **DOM ID**: `#marqueeContainer` / `#marqueeText`
* **規範要求**: 
  * 背景採用半透明深紅警告色 (`bg-red-950/90 border-red-500`)。
  * 文字內容格式固定為：`🔴【風管處公告】{official_title} ｜ 🤖 GEM 雙生模型裁定：{final_action} ｜ ⏱️ 官方對算視窗 ({updated_at})`

### 2.2 核心戰術 Header
* **數據綁定元件**:
  * 心跳計數：`#lblHeartbeat`
  * 實時時間：`#liveClock` (CST 時區 hh:mm:ss 滾動)
  * 當前日期：`#liveDate` (YYYY-MM-DD 星期格式)
  * 模型置信度：固定標示 `96.8%`

### 2.3 CCTV 實時傳輸狀態卡片 (CCTV Monitor)
* **規範**: 保持雙鏡頭 IP 監控條列（N 岸 192.168.1.102 / S 岸 192.168.1.101），預設狀態顯示 `🟢 LIVE (25 FPS)`。

### 2.4 MarineTraffic AIS 地圖與 HUD 卡片 (AIS Map & Vessel Tracking)
* **地圖容器規範**:
  * 高度固定為 `h-[500px]`，確保行動端與桌面端均具備足夠地圖可視區域。
  * **iframe URL 對焦參數**:  
    `https://www.marinetraffic.com/en/ais/embed/zoom:13/centerv:24.83500/centerh:121.94000/mmsi:416017708`
  * **視角偏置原則**: 緯度/經度偏置 (centerv:24.8350, centerh:121.9400) 與 Zoom:13，保證五福號原生卡片於左側展開時，右上角圖層切換按鈕 (`[ 㗊 ]`) 與龜山島海域完全獨立不重疊。
* **HUD 數據綁定**:
  * 五福號座標：`#txtCoordWufu`

### 2.5 7-Day 戰術對比矩陣 (Schedule Comparison Matrix)
* **Tab 切換按鈕**: `D0 今日` / `3-Day` / `7-Day` / `全部`
* **欄位結構**: 時段日期 | 預估海象 | 🏛️ 官方公告 | 🚢 常規客輪 | ⚡ 游擊調撥 | 🤖 GEM 裁示

### 2.6 雙岸物理數值與 2D 風場向量羅盤 (Physics & Canvas Compass)
* **側向比對表**: 涵蓋 Hs,pier (折算波高)、Weff (有效風速)、UKC (裕深)、FB (預留乾舷) 之南北岸門檻檢核。
* **2D Canvas 羅盤 (`#compassCanvas`)**:
  * 繪製風向攻角 (Δθ=50°) 弧線。
  * 繪製 Weff 翠綠色投影向量。

### 2.7 Windy 氣象圖場 (Windy Embed)
* **圖層切換**: 風速 (`wind`) / 浪高 (`waves`) / 降雨 (`rain`) / 氣壓 (`pressure`)。

### 2.8 碼頭剖面與 5 軸態勢雷達圖 (Profile & Radar Canvas)
* **Canvas ID**: `#profileCanvas` 與 `#radarCanvas`
* **切換模式**: 南岸 (`south`) / 北岸 (`north`) / 雙岸對比 (`compare`)。

---

## 🔄 3. 數據同化與更新介面規範 (Data Contract)

所有後端 Pipeline 執行完畢後，**嚴禁修改 HTML 模板**，僅能更新 JSON 數據檔案 `data/live_status.json` 及注入 `index.html` 中的初始化變數。

---

## 🔒 4. 變更控制原則 (Change Governance)
1. **結構凍結 (Layout Lock)**：禁止調整 DOM 階層關係、Tailwind 樣式類別及地圖高寬。
2. **數據驅動 (Data-Driven)**：所有指標變動一律經由 `main_orchestrator.py` 產出 JSON，由前端 JavaScript 輪詢同化。
3. **版本控管 (Version Assurance)**：每次數據與模型更新均需通過 AST 靜態語法檢測並自動同步至 GitHub Pages 根目錄 `/index.html`。
