# 🌊 GEM Engine UI/UX 儀表板架構與數據同化規範指南 (Dashboard Governance Standard)

> **版本**：v88.0 Flagship Standard
> **核心原則**：`Layout Frozen, Data Fluid`（UI/UX 版面結構剛性凍結，僅允許後端數據層動態注入更新）

---

## 📌 1. 規範宗旨 (Purpose)
本規範結合「宏觀外海預報降尺度」、「CWA測站/CCTV時域殘差」與「烏石港母港動態」，確立龜山島全域海事指揮中樞前端視覺面板的唯一標準結構。

---

## 🏛️ 2. 面板組件結構規範 (UI Component Specifications)
* **頂部跑馬燈**: `#marqueeContainer` / `#marqueeText` 警告與 80% RL 建議看板。
* **CCTV 狀態卡片**: 簡化標示 `CCTV IP N 燈號` 與 `CCTV IP S 燈號`，即時綠燈 LIVE (25 FPS)。
* **AIS MarineTraffic 地圖**: 容器高度固定為 `h-[500px]`，視角偏置 `centerv:24.83500/centerh:121.94000/zoom:13`。
* **風場 2D 羅盤與剖面圖**: Canvas 繪製攻角 Δθ=50° 與 Weff 翠綠色投影向量。
