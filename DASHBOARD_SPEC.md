# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.7 Official Date-Sync, 4-Way Consensus & Smart LINE Override Architecture
> **原則**：Spec-Driven, Code-Diff Minimal Push, Unified Mobile-First Design, 4-Way Arbitration, CST-Locked

## 🏛️ 1. 官方公告與日期對比表同步規範 (CST UTC+8)
1. **狀態隔離與同步 (`web_official_veto` vs `official_veto`)**：
   - 後端爬蟲偵測到官網或粉專發布今日封島時，寫入 `web_official_veto = 1` 與 `announcement_scope`（`FULL_DAY` 或 `AFTERNOON`）。
   - 前端定時更新海氣象 API 時，必須完整繼承 `web_official_veto`，嚴禁以數值預報覆寫清除官方封島公告。
2. **日期對比表 (`D0` / `D+1`) 雙向連動**：
   - 當 `web_official_veto == 1` 或人工覆寫鎖生效時，今日 `D0`（`07:30` / `11:30` / `16:30`）之「🏛️ 官方實質判定」同步切換為 `🔴 公告封島`（若為 `AFTERNOON` 下午封島半天，則 `07:30` 保留開島、`11:30` 與 `16:30` 同步轉為 `🔴 公告封島`）。
   - 當 `tomorrow_veto == 1` 時，今日 `D0` 維持實際營運狀態，僅同步將 `D+1 (明日)` 官方欄位切為 `🔴 官方公告封島`。
