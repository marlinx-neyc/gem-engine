# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.11 Wufu-Only Beacon Map, CWA Buoy Fusion & Cloud Hydration
> **原則**：Spec-Driven, Single-Vessel-Beacon-UI, Semantic-Hash Push, CWA-Buoy-First, CST-Locked

## 🏛️ 1. 純淨公務船單一標示與多源觀測融合規範
1. **公務船五福號單一標示 (`#wufuLeafletMap`)**：
   - 海圖視窗僅渲染「東北角五福號」雙層脈衝閃燈與名稱標籤，過濾所有無關漁船、商船與遮擋彈窗，確保行動端與桌面端一眼辨識公務船即時動態。
2. **CWA 浮標實測優先 (`O-B0075-001`)**：
   - 優先讀取龜山島浮標 (`46708A`) 與龍洞浮標 (`46694A`) 實測波高 $H_s$ 與湧浪週期 $T_p$，與 Open-Meteo 預報取保守最大值融合。
3. **語意狀態雜湊 (`state_hash`) 與雲端狀態回填**：
   - 僅當裁決狀態、官方公告、人工覆寫鎖、AIS 狀態、午後預警改變，或 $\Delta H_s \ge 0.05\text{m}$、$\Delta T_p \ge 0.5\text{s}$ 時才寫入 JSON 與推送 Git；啟動前先回填雲端既有覆寫鎖與 AIS 軌跡。
