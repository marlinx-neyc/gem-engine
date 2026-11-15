# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.13 Native MarineTraffic MMSI Lock, CWA Buoy Fusion & Cloud Hydration
> **原則**：Spec-Driven, Native-MarineTraffic-MMSI-Lock, Unobstructed-Close-Button, Semantic-Hash Push, CWA-Buoy-First

## 🏛️ 1. 原生 MarineTraffic AIS 鎖定與多源觀測融合規範
1. **原生 MarineTraffic MMSI 416017708 鎖定 (`#marineTrafficIframe`)**：
   - 採用原生 MarineTraffic 嵌入視圖 (`/mmsi:416017708`) 明確標示公務船「東北角五福號 (`DUNG BEI JIAU WU FU`)」目標圓圈與即時狀態，行動端透過寬視口縮放 (`scale(0.649)`) 確保右上角 `×` 關閉鈕完全露出不重疊。
2. **CWA 浮標實測優先 (`O-B0075-001`)**：
   - 優先讀取龜山島浮標 (`46708A`) 與龍洞浮標 (`46694A`) 實測波高 $H_s$ 與湧浪週期 $T_p$，與 Open-Meteo 預報取保守最大值融合。
3. **語意狀態雜湊 (`state_hash`) 與雲端狀態回填**：
   - 僅當裁決狀態、官方公告、人工覆寫鎖、AIS 狀態、午後預警改變，或 $\Delta H_s \ge 0.05\text{m}$、$\Delta T_p \ge 0.5\text{s}$ 時才寫入 JSON 與推送 Git。
