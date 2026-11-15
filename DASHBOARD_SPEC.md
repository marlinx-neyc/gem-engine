# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.8 State-Hash Anti-Bloat, Real-AIS Isolation & Hourly PM-Closure Forecast
> **原則**：Spec-Driven, Semantic-Hash Push, Real-AIS Ground Truth, Hourly Predictive Risk, CST-Locked

## 🏛️ 1. 防爆量差異寫入與即時性分流規範
1. **語意狀態雜湊 (`state_hash`)**：
   - 僅當裁決狀態、官方公告、人工覆寫鎖、AIS 狀態、午後預警改變，或浪高變動 $\Delta H_s \ge 0.05\text{m}$、週期變動 $\Delta T_p \ge 0.5\text{s}$ 時才執行原子寫入與 Git Push，避免無效 Commit 觸發 GitHub 次級限流。
2. **真實 AIS 權重隔離 (`is_real_ais`)**：
   - 僅當接通真實 AIS 座標 (`is_real_ais == True`) 且五福號靠泊碼頭時，才賦予「實船駐島鐵證」覆寫官網滯後公告之權限；水文推演船位僅供輔助參考，杜絕循環論證。
3. **逐時午後封島預判 (`pm_forecast`)**：
   - 透過 Open-Meteo `hourly` 序列計算未來 3 小時浪高上升斜率與 `12:00 - 17:00 CST` 峰值，提前於早盤標示午後半日封島高風險預警。
