# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.9 CWA Buoy Fusion, Cloud State Hydration & Full Embed URLs
> **原則**：Spec-Driven, Semantic-Hash Push, CWA-Buoy-First, Real-AIS Ground Truth, CST-Locked

## 🏛️ 1. 多源觀測融合與防覆蓋規範
1. **CWA 浮標實測優先 (`O-B0075-001`)**：
   - 優先讀取龜山島浮標 (`46708A`) 與龍洞浮標 (`46694A`) 實測波高 $H_s$ 與湧浪週期 $T_p$，與 Open-Meteo 預報取保守最大值融合，即時捕捉長湧浪繞射穿透 ($T_p \ge 12.0\text{s}$)。
2. **語意狀態雜湊 (`state_hash`) 與雲端狀態回填**：
   - 僅當裁決狀態、官方公告、人工覆寫鎖、AIS 狀態、午後預警改變，或 $\Delta H_s \ge 0.05\text{m}$、$\Delta T_p \ge 0.5\text{s}$ 時才寫入 JSON 與推送 Git；啟動前先回填雲端既有覆寫鎖與 AIS 軌跡。
3. **日夜間營運語意區隔**：
   - 船班營運時段 (`07:00 - 16:30 CST`) 顯示即時靠泊裁決；非營運時段 (`16:31 - 06:59 CST`) 明確標註「夜間休整期（預估開窗/管制）」。
