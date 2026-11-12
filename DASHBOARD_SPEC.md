# 🌊 GEM Engine UI/UX 儀表板與系統架構規範指南 (Dashboard Governance Standard)
> **版本**：v103.3 Real-Time Telemetry & Multi-Source Consensus Architecture
> **原則**：Spec-Driven, Code-Diff Minimal Push, Unified Mobile-First Design, CST-Locked, Live-API Direct

## 🏛️ 1. 官方三時段與多重驗證規範 (CST UTC+8)
- 🌅 **晨間首航巡查窗 (07:30)**：06:30 - 09:30 CST，比對五福號靠泊狀態與即時海氣象，決定早盤放行。
- ☀️ **午間巡查防禦窗 (11:30)**：10:30 - 13:30 CST，比對午後潮位加成與湧浪群速，決定是否防禦性早退。
- 🌇 **傍晚閉島休整窗 (16:30)**：15:30 - 18:30 CST，清島休整驗證與未來 7 日營運預報對齊。
- 🚢 **靠泊判定準則**：與碼頭距離 $\le 180\text{m}$ 且船速 $SOG \le 1.5\text{ knots}$ 為確認靠泊。
- 🌐 **雙軌即時數據流**：後端 Cron 定時寫入官方公告與 AIS 狀態；前端開啟或點擊「實時同步」時直連 Open-Meteo Marine & Weather API 動態更新所有物理指標與 7-Day 預報。

## 🏛️ 2. 面板 12 大戰術卡片全動態綁定規範
1. 雙軌多重驗證跑馬燈 (`#marqueeContainer`) 2. 戰術 Header (`#badgeHeartbeatContainer` 真實同步時戳)
3. CCTV 雙岸眼睛 (`#cctvCard`) 4. 🌀 颱風即時動態 (`#typhoonCard`) 5. 🌊 浪湧與氣壓監測視窗 (`#swellForecastCard`)
6. 🌐 MarineTraffic AIS 與五福號 HUD 7. 🌅 7-Day 完整動態預報對比表 8. 雙岸關鍵物理數值側向比對
9. 🧭 2D 風場向量羅盤 Canvas 10. 🌀 Windy 動態圖場 11. 📐 碼頭剖面越浪 Canvas 12. 🎯 5 軸態勢雷達 Canvas
