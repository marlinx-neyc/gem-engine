# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.6 4-Way Consensus, Long-Swell Diffraction & Smart LINE Override Architecture
> **原則**：Spec-Driven, Code-Diff Minimal Push, Unified Mobile-First Design, 4-Way Arbitration, CST-Locked

## 🏛️ 1. 四維綜合比對與仲裁優先權規範 (CST UTC+8)
1. **Priority 0 — 人工緊急覆寫鎖 (`manual_override`)**：
   - 值班人員透過面板貼上現場 LINE 群組緊急公告並寫入 GitHub API 後，自動解析「下午封島 (12:00-17:30)」或「全日封島 (07:00-17:30)」，鎖定最高優先權直至當日 `17:30 CST`，背景自動排程僅更新物理觀測數值，嚴禁覆蓋人工裁決。
2. **Priority 1 — 公務船路徑向量 (`agents/gem_vessel.py` Trajectory)**：
   - 船班營運時段 (`07:00 - 16:30 CST`) 內，若五福號航向西北西 ($250^\circ \le COG \le 320^\circ$) 且距島距離增加 $\Delta d > 300\text{m}$（`RETREATING_TO_WUSHI`），或島周繞行無法靠泊（`LOITERING_FAILED_DOCK`），立即判定**盤中臨時封島／疏散**。
3. **Priority 2 — 公務船靜態靠泊鐵證 (`is_docked_island`)**：
   - 營運時段內五福號靠泊北岸或南岸碼頭（距離 $\le 180\text{m}$ 且 $SOG \le 1.5\text{ knots}$），代表實質開島戒護中，自動覆寫修正官網滯後封島文字。
4. **Priority 3 — 水動力物理領先熔斷 (`core/gem_physics.py`)**：
   - 納入長週期湧浪 ($T_p \ge 12.0\text{s}$) 繞射穿透係數修正（南岸 $K_d=0.75$、北岸 $K_d=1.00$），當港池折算波高 $H_{s,\text{pier}}$（北 $\le 0.95\text{m}$ / 南 $\le 1.13\text{m}$）、有效風速 $W_{\text{eff}}$ 或預留乾舷 $FB \ge 0.50\text{m}$ 破線時提前發出物理熔斷預警。
5. **Priority 4 — 官方網頁/粉專跨日預告 (`agents/gem_scout.py`)**：
   - 帶入 `Cache-Control: no-cache` 與日期時效過濾器，負責隔日 (`D+1`) 預警封島與非營運時段行政管制。
