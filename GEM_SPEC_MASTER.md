# GEM_SPEC_MASTER.md
# GEM-V36D 龜山島數位雙生海事戰術控制台最高技術與戰術規範檔

**文件版本**：v36D.330.0 Three-Scheme & Guerrilla Vector Master Max Complete  
**生效日期**：2026-10-05  
**適用範疇**：後端 Python / UKF / PINN 算子、GitHub Actions 排程、`latest_decision.json` SSOT 封包、Desktop/Mobile UI 介面與 AI 智庫推理引擎。

---

## 1. 系統架構、角色合約與 SSOT 數據同步協議 (Architecture & SSOT Contract)

### 1.1 專家角色與責任合約
1. **專家定位**：本系統與 Agent 統合「周易象數、奇門遁甲、天文氣象學、海河工程學數值模型分析與建構」五大領域專家知識，為龜山島周邊海域水文、氣象實測與數值模擬之最高裁決機制。
2. **單一真實數據源 (SSOT)**：
   - 後端由 `main_orchestrator.py` 與 GitHub Actions 10 秒級排程組成唯一數據生產者，實時同化 CWA / WRF / Sentinel-1 / TDX AIS 數據並寫入 `latest_decision.json`。
   - 前端（`desktop.html`, `mobile.html`）與 AI Agent 為純數據消費者，強制透過 `cache: 'no-store'` 輪詢或 SSE 訂閱 `latest_decision.json`。
   - 任何後端排程或 AI 推理嚴禁覆蓋或篡改 `.html` 介面結構。

### 1.2 雙向握手校驗機制 (Handshake ACK)
- AI Agent 在生成任何報告前，必須向 `latest_decision.json` 發起狀態 ACK 校驗。
- 若 Agent 計算之 VETO 燈號與 `latest_decision.json` 衝突，Agent 必須修復殘差，無條件採納 JSON 數據作為唯一 Ground Truth。

---

## 2. 周易曆法與水動力算子精算矩陣 (Physics & I Ching Matrix)

### 2.1 剛性熔斷邏輯
總體裁決 $Q_{final}$ 遵從一票否決（Hard VETO）原則：
$$\text{Hard\_Veto} = \text{Veto}_{Hs} \lor \text{Veto}_{W} \lor \text{Veto}_{UKC} \lor \text{Veto}_{FB}$$

$$\text{若 } \text{Hard\_Veto} = \text{True} \implies Q_{final} = \text{Q4 (0.0\% 物理熔斷 / 全線封島)}$$

### 2.2 四層物理防線算子與周天公度同化

| 算子名稱 | 符號 | 精算公式 / 遲滯函數 | 剛性通過門檻 | 周易與天文曆法對齊 |
| :--- | :--- | :--- | :--- | :--- |
| **碼頭有效波高** | $H_{s,pier}$ | $H_{s,pier} = H_{s,CWA} \cdot K_d(T_p) + PINN_{offset}$<br>若 $T_p > 12.0\text{s} \implies K_d = 1.00$<br>若 $11.5\text{s} \le T_p \le 12.0\text{s} \implies K_d = 0.883 + 0.234(T_p - 11.5)$ | $H_{s,pier} \le 1.20 \cdot \alpha_{tune}\text{ m}$ | 兌宮/驚門（$T_p > 12.0\text{s}$ 港池共振穿透） |
| **攻角有效風速** | $W_{eff}$ | $W_{eff} = W_{local} \cdot \vert{}\cos(\Delta\theta)\vert{} \cdot K_w$<br>若 $\Delta\theta \ge 45.0^\circ \implies K_w = 1.00$<br>若 $30.0^\circ \le \Delta\theta < 45.0^\circ \implies K_w = 0.78 + 0.0147(\Delta\theta - 30.0)$ | $W_{eff} \le 10.80 \cdot \alpha_{tune}\text{ m/s}$ | 巽宮/杜門（$\Delta\theta \ge 38^\circ$ 巽風移防） |
| **動態富餘水深** | $UKC$ | $UKC = [(d_{chart\_base} + d_{chart\_offset}) + \eta_{tide}] - (d_{draft} + S_{squat}) - H_{s,pier}$<br>含雙體船蹲沉量 $S_{squat} = 0.82\text{ m}$ | $UKC \ge 1.50\text{ m}$ | 坤宮/死門（低潮位底撞 VETO 熔斷） |
| **預留乾舷高度** | $FB_{pier}$ | $FB_{pier} = BASE\_FREEBOARD - \eta_{tide}$<br>若 Vision-PINN 偵測越浪率 $> 0\text{ p/min} \implies FB_{pier} = 0.15\text{ m}$ | $FB_{pier} \ge 0.50\text{ m}$ | 乾/坎宮（滿潮越浪硬覆寫） |

*註：$\alpha_{tune}$ 為 Sigmoid 神經網路自適應門檻緊縮係數（$0.65 \le \alpha_{tune} \le 1.00$）。周天 360 度公度年算子每季 90°、每節 45°、每氣 15°、每候 5° 精確扣合氣象場。

---

## 3. 奇門 70% 門控與高維水動力算子 (Qimen 70% Gate & Level 5/7)

### 3.1 奇門 70% 門控同化機制 ($Q_{consensus}$)
- 當奇門氣場同化率 $Q_{consensus} \ge 70.0\%$ 時，解鎖 64D 量子拓撲參研提醒（最大 35% 偏置）。
- **八門戰術導引**：
  1. **開門/休門（乾/坎宮）**：$Q_{consensus} \ge 70\%$, $\Delta\theta < 35^\circ \implies$ 穩定靠泊【北岸碼頭】。
  2. **杜門（巽宮）**：$\Delta\theta \ge 38^\circ \implies$ T-30 移防【南岸權宜碼頭】。
  3. **驚門（兌宮）**：$T_p > 12.0\text{s} \implies$ T-45 湧浪預警，$K_d \to 1.00$。
  4. **死門（坤宮）**：物理 Hard VETO 超標 $\implies$ 剛性熔斷直航【烏石港】。

### 3.2 Level 5 高維算子與 Level 7 水動力矩陣
- **Level 5 高維算子組**：
  1. `VisionPINNEdgeNet`：128x128 視角張量估算越浪率 `vision_overtopping_rate_pmin`（p/min）。
  2. `VesselMMSIHydrodynamics`：對齊 MMSI 船隻（如凱鯨號），精算吃水與 $S_{squat}=0.82\text{m}$ 及 Roll/Pitch 角。
  3. `FNO1dWaveSpectralForecaster`：100ms 傅立葉神經算子推演未來 3 小時波高演化 `fno_forecast_mean_hs_m`。
  4. `QuantumTopology64DEngine`：64D 拓撲同化，輸出量子相干性 `quantum_topology_coherence`。
  5. `MultiAgentSwarmDispatcher`：強化學習賽局，輸出多船靠泊指派 `swarm_dispatch_plan`。
- **Level 7 南北角雙碼頭與潮汐算子**：
  - **南北角雙碼頭水動力矩陣**：獨立解算北岸主碼頭與南岸權宜碼頭之波高、風速、流速向量（如 $1.4\text{ kts} \nwarrow \text{NW } 315^\circ$），背風角 $\Delta\theta < 45^\circ$ 且 $H_{s,pier} \le 1.20\text{ m}$ 時授權游擊切換至南岸碼頭。
  - **天文潮差動態扣減算子**：朔望大潮（總潮差 1.80m，滿潮 +1.35m / 乾潮 -0.45m），乾潮扣減 0.45m $UKC$，滿潮扣減 1.35m $FB_{pier}$。

---

## 4. 游擊式動態調度與特區避險時窗演算法 (Dispatch & Hazard Rules)

### 4.1 游擊式時間軸與撤離時間算定
- **上午場（07:30–11:30）**：北岸越浪且 $\Delta\theta < 45^\circ \implies$ 08:30 班次改靠【南岸權宜碼頭】或延滯登至 10:00。
- **下午場（12:00–17:30）**：風向轉 ESE（$\Delta\theta \ge 45^\circ$）或 $T_p > 12.0\text{s} \implies$ 啟動雙預警（10:50/13:50 廣播、11:20 止登、14:20 強制清島撤離至烏石港）。
- **撤離時間算定公式**：
  $$Evac\_Minutes = \left\lceil \frac{15}{Passenger\_Count} + \max(0, (S_{squat} - 0.50) \cdot 15) + 15 \right\rceil$$

### 4.2 牛奶海熱泉避險時窗
- **峰值時間**：$T_{peak} = T_{HighTide} + 3.5\text{h}$
- **避險視窗**：$T_{peak} \pm 1.5\text{h}$（強酸羽狀流 pH 1.75~2.0 擴散期，全線暫停 SUP 與水下活動，保持 200m 安全距離）。

---

## 5. Gymnasium 強化學習 (RL) 與先驗氣候智庫 (RL & Climate Lake)

### 5.1 狀態與動作空間
- **狀態空間 ($S \in \mathbb{R}^{10}$)**：
  $$S = [H_{s,pier}, W_{local}, UKC, FB_{pier}, T_p, \theta_{wave}, Swell\_Ratio, S_{cos}, \eta_{surge}, K_d]$$
- **動作空間 ($A \in \{0, 1, 2, 3\}$)**：
  - `0`: Q1 (全線開放)
  - `1`: Q2 (條件靠泊)
  - `2`: Q3 (預警限制)
  - `3`: Q4 (全線封島 / NO_DISPATCH)

### 5.2 獎勵函數 ($R(s, a)$)
- 若 $\text{VETO\_Pass} = \text{True}$ 且 $a = 0 \implies R = +150$
- 若 $\text{VETO\_Pass} = \text{False}$ 且 $a = 3 \implies R = +100$
- 若 $\text{VETO\_Pass} = \text{False}$ 且 $a \in \{0, 1, 2\} \implies R = -9999$（致命懲罰）

---

## 6. 前端 UI/UX 幾何凍結與手持端全規範 (`mobile.html` Master Specification)

### 6.1 CLS = 0 版面幾何凍結與解耦原則
- 全數 HTML 卡片容器設定 `contain: strict` 或 `contain: content`。
- 前端 JS 僅允許透過 `node.textContent` 寫入純文字，嚴禁使用 `innerHTML` 重新拼接 DOM。
- **實體測站與數值模型解耦**：前 4 列僅展示純 CWA 實測數值（風級風速、波高週期、海況）與官方判定燈號（`🔴 官方封島` / `🟢 母港安全`）；第 5 列獨立全寬呈現 **🤖 GEM-V36D 物理數值預測模型** 與專屬熔斷標籤。
- 移除原先兩個被要求刪除的 Canvas 圖表（未來三日折線圖 Canvas 與心跳脈衝 ECG 波形 Canvas），改用高資訊密度 Table-Based 結構。

### 6.2 雙時鐘、心跳燈與 Watchdog 規範
1. **設備秒針與實時日期**：原生 1000ms 跳動，頂部常駐明確日期（如 `2026-10-05` CST）。
2. **心跳呼吸燈 (SSE Heartbeat)**：四大實體測站與 GEM 模型配置綠色脈衝呼吸燈（`pulse-dot-green` / `pulse-dot-blue`），與 10s 異步 SSE 數據綁定，標註實時資料新鮮度（如 `即時 1s前`）。
3. **Watchdog 數據過期阻斷**：若超過 30 秒未接收到新 JSON，頂部燈號切換為「🔴 數據過期 (OUT OF DATE)」，並彈出半透明警告 Banner。

### 6.3 區塊 6：南北岸碼頭即時水文矩陣階層規範
- **【上列】官方觀測值與法定標準檢核**：彙整 CWA 實測平均風/陣風（限值 $\ge 6$ 級）、沿海波高大浪限值（$\ge 2 \sim 3\text{ m}$）、長浪警報（$T_p \ge 8\text{s}$ 且 $H_{s,pier} \ge 1.5\text{ m}$）與海上颱風警報狀態，右側並排顯示 `🔴 官方預報封島` 燈號。
- **【下列】GEM-V36D 物理數值算子精算**：微觀解析攻角有效風速 $W_{eff}$、碼頭有效波高 $H_{s,pier}$、長浪港池共振消能（$K_d = 1.00$）、滿潮乾舷 $FB_{pier}$（越浪覆寫至 $0.15\text{ m}$）、動態富餘水深 $UKC$ 及航線表面潮流向量（$1.4\text{ kts} \nwarrow \text{NW } 315^\circ$）。
- **【末列】雙軌燈號與最終游擊方案**：對稱並列官方判定燈號與 GEM 智庫裁決燈號，底端給出明確戰術指引（迎風巨浪嚴禁靠泊北岸、長浪穿透雙岸失效直航返航烏石港）。

### 6.4 區塊 7：二合一整合與當日突發變量推演矩陣
- **表圖同版二合一**：將 2x2 時間線預測矩陣、當日突發性海象變量推演表與六角全維度安全雷達圖統合於單一卡片 `7. 🎯 2x2 時間線預測矩陣與全維度戰術安全雷達圖`。
- **當日關鍵突發變量同化**：
  - 12:00 局域風向突轉 ESE 110°（$\Delta\theta=58^\circ$ 屏障崩潰）。
  - 全天遠洋湧浪 $T_p=15.5\text{ s} > 12.0\text{ s}$ 港池消能完全失效（$K_d=1.00$）。
  - 滿潮 $+1.25\text{ m}$ 乾舷壓迫至 $FB_{pier}=0.15\text{ m}$（Vision-PINN 越浪率 $1.31\text{ p/min}$）。
  - 牛奶海強酸熱泉 $11:12 \sim 14:12$（$T_{peak}=12:42$）避險時窗。
- **時段連動雷達圖**：點選任一時段按鈕（`08:00`、`10:00`、`11:20 止登`、`12:00`、`14:20 撤離`、`16:00`），預測表與原生 Canvas 雷達圖即時同步重繪，六軸端點明確標註實測載荷、剛性限值與 PASS/FAIL 標籤。
- **清除未渲染 LaTeX 亂碼**：文字區塊嚴禁輸出未經渲染之原始 LaTeX 代碼（如 `$H_s > 1.13\text{m}$`），一律採用乾淨標準之 HTML 標籤（如 `<b>Hs 3.71m &gt; 1.13m</b>`）。

---

## 7. 標準 SSOT JSON Data Exchange Schema (`latest_decision.json`)

```json
{
  "version": "v36D.330.0 Three-Scheme & Guerrilla Vector Master Complete",
  "timestamp": "2026-10-05 08:30:00 CST",
  "confidence_label": "🟢 100.0% [完整同化 PASS]",
  "decision": "🔴 0.0% 物理 VETO 熔斷 / 全線封島",
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
    "hs_cwa": 3.71,
    "w_cwa": 8.50,
    "hs_pier_m": 3.71,
    "w_local_ms": 8.50,
    "w_eff_ms": 5.46,
    "tp_s": 15.5,
    "delta_theta_deg": 50.0,
    "tide_eta_m": 1.00,
    "alpha_adaptive": 0.94,
    "eff_hs_limit": 1.13,
    "eff_weff_limit": 10.17,
    "eff_ukc_limit": 1.50,
    "eff_fb_limit": 0.50,
    "ukc_m": 3.77,
    "fb_pier_m": 0.15,
    "pass_hs": false,
    "pass_w": true,
    "pass_ukc": true,
    "pass_fb": false,
    "has_veto": true
  },
  "guerrilla_dispatch": {
    "berthing_pier": "無 (雙岸失效，禁止靠泊)",
    "evacuation_pier": "無 (雙岸失效，直航返航烏石港)",
    "guerrilla_mode": "BOTH_PIERS_DISABLED",
    "morning_tactic": "🚨 全線熔斷：港池波高 3.71m 超標，雙岸碼頭失效禁止靠泊",
    "afternoon_tactic": "🚨 撤離執行：雙岸越浪嚴重，11:20 止登，14:20 全員撤離至【烏石港】",
    "tactical_summary": "🔴 第一位階 Hard VETO 剛性熔斷（Hs=3.71m）。全天禁止登島與靠泊，預計撤離耗時 20 分鐘。"
  },
  "level5_advanced_metrics": {
    "vision_overtopping_rate_pmin": 1.31,
    "vision_kd_bias": 0.0295,
    "vessel_hydrodynamics": {
      "vessel_name": "凱鯨號 (穿浪雙體船)",
      "vessel_type": "CATAMARAN",
      "dynamic_squat_m": 0.82,
      "roll_deg": 3.3,
      "pitch_deg": 4.4
    },
    "fno_forecast_mean_hs_m": 1.58,
    "quantum_topology_coherence": 0.4682
  },
  "qimen_macro_consensus": {
    "consensus_rate_pct": 100.0,
    "macro_advisory_enabled": true,
    "octagram_gate_state": "死門 (坤宮 - 剛性熔断直航烏石港)",
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 100.0% (>=70%)，已啟動 35% 宏觀參研偏置與【死門 (坤宮)】戰術導引"
  }
}
