# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.12 Multi-Layer Sea Chart, Unobstructed MarineTraffic & CWA Buoy Fusion
> **原則**：Spec-Driven, Multi-Layer-Keyless-Map, Pinpoint-Wufu-Beacon, Semantic-Hash Push, CWA-Buoy-First

## 🏛️ 1. 多圖層海圖與單一公務船標示規範
1. **四圖層自由切換 (`#wufuMapWrapper`)**：
   - 支援「🌑 暗色海圖 (Esri Dark + OpenSeaMap 航標)」、「🛰️ 衛星海圖」、「🗺️ 航海圖」與「🌐 原版AIS底圖 (MarineTraffic 無白卡遮擋模式)」。
   - 座標中心精準對齊光點核心 (`iconAnchor: [10, 10]`)，僅顯示「東北角五福號（名稱 + 雙層脈衝閃燈）」，且不遮擋任何操作按鈕。
2. **CWA 浮標實測優先 (`O-B0075-001`)**：
   - 優先讀取龜山島浮標 (`46708A`) 與龍洞浮標 (`46694A`) 實測波高 $H_s$ 與湧浪週期 $T_p$，與 Open-Meteo 預報取保守最大值融合。
3. **語意狀態雜湊 (`state_hash`) 與雲端狀態回填**：
   - 僅當裁決狀態、官方公告、人工覆寫鎖、AIS 狀態、午後預警改變，或 $\Delta H_s \ge 0.05\text{m}$、$\Delta T_p \ge 0.5\text{s}$ 時才寫入 JSON 與推送 Git。
