# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.10 Unobstructed AIS Map, CWA Buoy Fusion & Cloud Hydration
> **原則**：Spec-Driven, Unobstructed-Mobile-Map, Semantic-Hash Push, CWA-Buoy-First, CST-Locked

## 🏛️ 1. 行動端 AIS 海圖無遮擋與多源觀測融合規範
1. **MarineTraffic 行動端防遮擋視窗**：
   - 預設採用「海圖全景模式」（`centerv:24.85500/centerh:121.89500/zoom:12/shownames:true`），不自動彈出大型白卡遮擋船位；切換「五福號卡片模式」時，手機端自動套用虛擬寬視口縮放 (`scale 0.65`)，確保卡片右上角 `×` 關閉鈕不被地圖圖層按鈕重疊覆蓋。
2. **CWA 浮標實測優先 (`O-B0075-001`)**：
   - 優先讀取龜山島浮標 (`46708A`) 與龍洞浮標 (`46694A`) 實測波高 $H_s$ 與湧浪週期 $T_p$，與 Open-Meteo 預報取保守最大值融合。
3. **語意狀態雜湊 (`state_hash`) 與雲端狀態回填**：
   - 僅當裁決狀態、官方公告、人工覆寫鎖、AIS 狀態、午後預警改變，或 $\Delta H_s \ge 0.05\text{m}$、$\Delta T_p \ge 0.5\text{s}$ 時才寫入 JSON 與推送 Git；啟動前先回填雲端既有覆寫鎖與 AIS 軌跡。
