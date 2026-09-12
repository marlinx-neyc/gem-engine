# GEM-V36D 數位雙生海事戰術智庫 — 全域 SSOT 代碼自我稽核與開發規範 (v36D.13.0 Level 5)

本規範為 GEM-V36D (v36D.13.0 Level 5 Complete) 數位雙生海事戰術控制台（包含 Desktop、Mobile 端與後端 AI 智庫）之最高代碼與 UI/UX 標準。本版本全面整合物理遙測、PINN 剛性防線、游擊移防、奇門 70% 參研門控與 Level 5 五大高維邊緣算子。

---

## 一、 系統哲學與數據解耦原則 (Philosophy & Architecture)

1. **數據與 UI 完全解耦**：AI 運算引擎（Python/Colab/GitHub Actions）作為數據生產者，輸出標準 SSOT `latest_decision.json`；前端網頁（`desktop.html`、`mobile.html`）純粹作為視覺渲染器，嚴禁在前端寫死業務邏輯。
2. **單一真實數據源 (SSOT Consensus)**：全站數據門檻與裁決指標，徹底以 JSON 資料為準，雙端數據顯示保持 100% 一致。

---

## 二、 全域 UI 視覺、色彩與圖表繪製規範 (Global UI & Styling)

全站介面統一採用暗色科技風 (Dark Tech) 佈局，視覺元件與色彩定義如下：

* **背景主色 (`#0b1120`)**：全站頁面與外層容器底色。
* **卡片背景 (`#1e293b`) / 深色框線 (`#334155`)**：戰術資訊卡片之背景與邊框。
* **圖表網格背景橫線 (`rgba(51, 65, 85, 0.5)`)**：所有 ECharts 圖表之 `splitLine` 樣式，統一設為 50% 透明度，避免線條過亮刺眼。
* **游標懸浮動態提示 (Hover Tooltip)**：圖表必須配置 `axisPointer: { type: 'cross' }` 交叉追蹤線，懸浮時精確顯示 Hs 波高、Wind 風速、UKC 裕深、Tp 週期與當下戰術判準。
* **戰術藍 (`#38bdf8`)**：專用於區塊標題、卡片邊框高亮、不確定性 σ 指標與連線狀態點。
* **警戒紅 (`#ef4444`)**：專用於 VETO 觸發、VETO 徽章、全線封島標籤與圖表警戒水平線。
* **安全綠 (`#10b981`)**：專用於 Q1 放行狀態、PASS 合格徽章、精確度提升幅度 (+%) 與 Level 5 算子卡片。
* **高光黃 (`#facc15`)**：專用於戰術裁決總結、Ground Truth 方案 C 評估結論與關鍵極限數值。
* **警戒橘 (`#f59e0b`)**：專用於游擊動態調度卡片邊框、風速警戒線與下午預警時窗。
* **紫光 (`#a855f7` / `#c084fc`)**：專用於奇門氣場卡片邊框、64D 量子拓撲相干性與長浪週期線。

---

## 三、 桌面端 (`desktop.html`) 剛性佈局與卡片順序 (v36D.13.0)

採用頂部整合導覽列與 32% / 68% 剛性雙欄佈局：

### 1. 頂部整合標題列 (`header-bar`)
* **智庫狀態與連線點**：展示 `GEM-V36D (v36D.13.0 Level 5) 戰術智庫` 與動態藍色呼吸燈。
* **升格雙核指標區**：整合 AI 信心指數 (100.0%)、不確定性 σ 方差 (0.3125)、精確度提升 (+58.4%) 與微觀/宏觀雙色動態權重進度條，釋放左欄空間。
* **通訊與時間戳記**：顯示成功通訊次數與即時更新秒數。

### 2. 左側戰術控制欄 (32% 欄寬) 剛性卡片順序 (由上至下共 5 張)
1. **即時水文與剛性門檻比對卡片 (PINN Engine)**：包含 Hs Pier、Wind Local、UKC、FB Pier 之數值與 PASS/VETO 狀態徽章。
2. **當日船班官模燈號比對與最後判斷卡片**：包含海象對比標準值（如 Hs <= 1.20m, W <= 10.80m/s, Delta_theta < 45deg）、官方 vs GEM 判斷與精確時間點戰術處置。
3. **⚓ 游擊式動態調度與時窗預判卡片 (`#f59e0b` 邊框)**：展示建議靠泊碼頭、撤離碼頭、戰術調度總結、上午時窗告示與下午時窗預警。
4. **🌀 颱風與奇門宏觀氣場預判專區 (`#a855f7` 邊框)**：展示颱風距離、2D 氣壓梯度與奇門 70% 匹配率狀態提示。
5. **🚀 Level 5 邊緣視覺、水動力與賽局算子卡片 (`#10b981` 邊框)**：展示 CV 視覺越浪率、MMSI 客輪沉降 (Squat)、FNO 100ms 預報波高、64D 量子拓撲相干性與 Swarm 多船賽局排隊摘要。

### 3. 右側動態圖表陣列 (68% 主畫廊)
* **2x2 時間線圖表陣列**：Hs 波高、Wind 風速、UKC 裕深、Tp 週期 4 張圖表，注入 11:00 與 16:00 決策虛線，背景橫線維持 50% 透明度。
* **未來七天雙軸趨勢預判圖表**：雙 Y 軸同步注入 Hs <= 1.20m 與 Wind <= 10.80m/s 雙警戒線。
* **戰略三方案評估 (Ground Truth)**：地位於右側底部，比對方案 A (官方)、B (監測)、C (GEM)，方案 C 採用高光黃 (`#facc15`) 高亮。

---

## 四、 手機端 (`mobile.html`) 輕量化卡片流規範 (v36D.13.0)

採用 100% 垂直單欄卡片流，嚴禁加載 ECharts DOM 以保證弱網極速載入：

1. **頂部連線狀態卡片**：包含 `● LIVE SSOT` 動態藍色呼吸燈與連線計數。
2. **Watchdog 數據過期 Banner (`#staleAlertMob`)**：遙測停滯 > 30 秒時自動彈出紅色警示。
3. **Q-Mode 戰術裁決 Banner (`#vetoBannerMob`)**：紅/綠動態底色高亮當前裁決。
4. **AI 雙核相對精確度與注意力閘卡片 (`#38bdf8` 邊框)**。
5. **即時海象數值與剛性門檻比對卡片 (PINN Engine)**。
6. **當日船班官模燈號比對與時窗動態處置卡片**。
7. **⚓ 游擊式動態調度與時窗預判卡片 (`#f59e0b` 邊框)**：顯示靠泊與撤離實體碼頭。
8. **🌀 颱風與奇門宏觀氣場預判專區 (`#a855f7` 邊框)**。
9. **🚀 Level 5 邊緣視覺、水動力與賽局算子卡片 (`#10b981` 邊框)**。
10. **戰略三方案評估卡片 (Ground Truth)**。
11. **裝置視角切換導覽列**。

---

## 五、 遊擊式動態調度與奇門 70% 參研門控機制

### 1. 游擊式實體碼頭鎖定矩陣 (Guerrilla Berthing Matrix)
* **常規靠撤**：海象良好，`berthing_pier` 與 `evacuation_pier` 均鎖定為【北岸主碼頭】。
* **上午游擊調撥**：北岸越浪但背風屏障有效（Delta_theta < 45deg），`berthing_pier` 鎖定為【南岸權宜碼頭】。
* **下午游擊撤退**：預測午後 ESE 巽宮風陣（Delta_theta >= 45deg）或長浪穿透（Tp > 12.0s），`evacuation_pier` 鎖定為【南岸權宜碼頭】，11:20 止登，14:20 強制清島撤離。
* **雙岸屏障失效**：觸發 PINN 剛性 VETO 阻斷，雙碼頭皆顯示【無 (雙岸失效，直航返航烏石港)】。

### 2. 奇門 70% 宏觀參研門控 (Qimen 70% Macro Advisory Gate)
* 當奇門氣場與物理場歷史同化匹配率 >= 70% 時，自動啟用 `qimen_macro_consensus` 參研提醒，將奇門預警文字注入前端面板。

---

## 六、 Level 5 五大高維進化算子規格

1. **Vision-PINN 邊緣視覺算子 (`VisionPINNEdgeNet`)**：解析 128x128 影像張量，估算實時越浪率 (p/min) 並提供 Kd 殘差微調。
2. **MMSI 專屬水動力算子 (`VesselMMSIHydrodynamics`)**：依船隻 MMSI 計算 Heave/Roll/Pitch 姿態與 Shallow-Water Dynamic Squat 沉降量，扣減 UKC 裕深。
3. **FNO 100ms 超速預報算子 (`FNO1dWaveSpectralForecaster`)**：1D 傅立葉神經算子，於 100ms 內預測未來 3 小時港池平均波高演化。
4. **Swarm 多船隊賽局調度器 (`MultiAgentSwarmDispatcher`)**：強化學習多智慧體賽局，自動規劃多艘客輪之靠泊與延滯順序。
5. **64D 太乙奇門量子拓撲同化器 (`QuantumTopology64DEngine`)**：將 36D 物理場擴充至 64D 高維時空拓撲，計算量子相干性 (Coherence)。

---

## 七、 SSOT JSON Schema 規範 (v36D.13.0 Complete)

前端 `window.onSSOTDataReceived(data)` 必須完整解析以下全新 Schema 結構：

```json
{
  "version": "v36D.13.0 Level 5 Complete",
  "timestamp": "2026-09-12 20:15:00 CST",
  "decision": "🔴 封島/防颱",
  "confidence_score": 100.0,
  "hard_veto_alert": true,
  "precision_metrics": {
    "converged_sigma": 0.3125,
    "precision_gain_pct": 58.4
  },
  "attention_gate": {
    "micro_physics_weight": 65.0,
    "macro_qimen_weight": 35.0
  },
  "physics_metrics": {
    "hs_pier_m": 3.71,
    "w_local_ms": 8.50,
    "ukc_m": 5.84,
    "fb_pier_m": 2.00,
    "has_veto": true
  },
  "guerrilla_dispatch": {
    "berthing_pier": "無 (雙岸失效，禁止靠泊)",
    "evacuation_pier": "無 (雙岸失效，直航返航烏石港)",
    "guerrilla_mode": "BOTH_PIERS_DISABLED",
    "morning_tactic": "⚠️ 上午游擊調撥：北岸越浪，08:30 班次改至【南岸權宜碼頭】靠泊",
    "afternoon_tactic": "🚨 下午游擊撤退：預測午後 ESE 巽宮風陣，11:20 止登，14:20 全員撤離",
    "tactical_summary": "執行「下午游擊撤退【南岸碼頭撤離】」"
  },
  "level5_advanced_metrics": {
    "vision_overtopping_rate_pmin": 1.31,
    "vision_kd_bias": 0.0295,
    "vessel_hydrodynamics": {
      "vessel_name": "凱鯨號 (穿浪雙體船)",
      "vessel_type": "CATAMARAN",
      "dynamic_squat_m": 0.86,
      "roll_deg": 3.3,
      "pitch_deg": 4.4
    },
    "fno_forecast_mean_hs_m": 1.58,
    "quantum_topology_coherence": 0.4682,
    "swarm_dispatch_plan": [
      { "agent_id": 1, "vessel_label": "凱鯨號 (Agent 1)", "assigned_pier": "無 (雙岸失效)", "tactical_action": "直航返航烏石港" }
    ]
  },
  "qimen_macro_consensus": {
    "consensus_rate_pct": 100.0,
    "macro_advisory_enabled": true,
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 100.0% (>=70%)，已啟動宏觀參研決策與預警提示"
  }
}
