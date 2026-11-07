# 🌊 GEM Engine UI/UX 儀表板架構與數據同化規範指南 (Dashboard Governance Standard)

> **版本**：v88.0 Flagship Standard
> **核心原則**：`Layout Frozen, Data Fluid`（UI/UX 版面結構剛性凍結，僅允許後端數據層動態注入更新）

---

## 📌 1. 規範宗旨 (Purpose)
本規範確立「龜山島全域海事戰術指揮中樞」前端視覺面板的唯一標準結構。後續所有演算法更新或數據對算，均不得修改前端 DOM 結構與 CSS 佈局，所有動態數值一律透過 `data/live_status.json` 與 `window.INITIAL_LIVE_DATA` 自動刷寫。

---

## 🏛️ 2. 面板組件結構規範 (UI Component Specifications)
* **頂部跑馬燈**: `#marqueeContainer` / `#marqueeText` 警告看板。
* **AIS MarineTraffic 地圖**: 容器高度固定為 `h-[500px]`，視角偏置 `centerv:24.83500/centerh:121.94000/zoom:13`，避免視訊卡與右上角按鈕 (㗊) 重疊。
* **風場 2D 羅盤與剖面圖**: Canvas 渲染攻角 Δθ=50° 與 Weff 翠綠色投影向量。
