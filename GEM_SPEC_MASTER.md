# GEM-V36D (v36D.13.0 Level 5 Master Final) 全域 SSOT 代碼自我稽核與開發規範

本規範為 GEM-V36D 數位雙生海事戰術控制台（Desktop 端、Mobile 端與 Python 主控算子）之最高技術標準。全系統維運與程式碼變更必須 100% 恪守「版面幾何固定化 (CLS = 0)」與「數據單向更新化 (Data-Only SSOT)」雙柱原則。

---

## 一、 系統哲學：版面固定化與數據更新化雙柱原則 (Core Pillars)

### 1. 版面固定化原則 (Layout Lockdown Specification / CLS = 0)
* **CSS Containment 座標鎖定**：全視角 HTML 元件（`desktop.html`、`mobile.html`、`index.html`）所有卡片與容器必須設定 `contain: strict` 或 `contain: content` 樣式屬性，徹底隔絕 DOM 幾何重排與重繪。
* **Zero-Reflow 純文字節點寫入**：前端 JavaScript 在進行 5 秒定時數據更新時，**僅允許使用 `node.textContent` 替換純數據文字**與動態切換既有 Style 顏色（如綠/黃/紅燈號），**絕對禁止使用 `innerHTML` 重新拼接或動態增刪 DOM 節點**。
* **永久零版面位移 (CLS = 0)**：卡片高度、寬度、Grid 網格與 Margin 間距於 CSS 中實體鎖定，數據長短變更不得引發任何元件尺寸伸縮或累積版面位移。

### 2. 數據更新化原則 (Data-Only Updating & Single Source of Truth)
* **後端純數據生產者**：後端 AI 算子（`main_orchestrator.py`）、Colab 訓練腳本與 GitHub Actions 定時工作流，純粹作為數據生產者，僅對接產出與 Commit 標準 SSOT 檔 `latest_decision.json`。
* **後端絕不觸碰介面**：後端 Python 程式碼與自動化腳本**嚴禁覆蓋、重寫或生成任何 `.html` 前端檔案**。
* **前端純數據渲染器**：前端頁面純粹透過 AJAX / Fetch 靜態輪詢 `latest_decision.json`，全站數據門檻、燈號與戰術決策徹底以該 JSON 數據為單一真實來源。

---

## 二、 全域 UI 視覺、色彩與 Hover 游標互動規範 (Global UI & Styling)

採用暗色科技風 (Dark Tech) 佈局，色彩與圖表互動定義如下：

* **背景主色 (`#0b1120`) / 卡片背景 (`#1e293b`) / 深色框線 (`#334155`)**：基底視覺。
* **戰術藍 (`#38bdf8`)**：標題、邊框高亮與不確定性 σ 指標。
* **警戒紅 (`#ef4444`)**：VETO 觸發、封島標籤與 Hs / UKC 警戒水平線。
* **安全綠 (`#10b981`)**：放行狀態、PASS 徽章與 Level 5 算子外框。
* **高光黃 (`#facc15`)**：戰術裁決總結、Ground Truth 方案 C 評估與 Hs 警戒線 (1.20m)。
* **警戒橘 (`#f59e0b`)**：游擊調度卡片邊框、Wind 風速警戒線 (10.80m/s) 與時窗預警。
* **紫光 (`#c084fc`)**：奇門卡片邊框、64D 量子拓撲相干性與 Tp 長浪週期警戒線 (12.0s)。
* **ECharts 互動與游標規範**：
  * 所有 ECharts 圖表 `splitLine` 統一設為 50% 透明度 (`rgba(51, 65, 85, 0.5)`)。
  * 圖表統一配置 `axisPointer: { type: 'cross' }` 追蹤線，懸浮 Tooltip 精確顯示時間、數值、燈號與當下戰術狀態。
  * 垂直時間判點虛線 (11:00 止登 / 14:00 撤離) **必須關閉端點箭頭 (`symbol: 'none'`)**。
  * **警戒線統一採用虛線 (`type: 'dashed'`)**，並標註明確數值標籤（Hs 1.20m、Wind 10.80m/s、UKC 1.50m、Tp 12.0s）。
  * 圖表需顯示 Legend 圖例，可點擊卡片與連結統一加入 `cursor: pointer` 樣式。

---

## 三、 桌面端 (`desktop.html`) 頂部一體化與 32% / 68% 剛性雙欄規範

### 1. 置頂一體化整合主卡片 (`header-master-card`)
* **同一列頂部大整合**：橫向併入主標題（含 `● LIVE SSOT` 動態藍呼吸燈與連線計數）、**🚀 Level 5 邊緣視覺、水動力與賽局高維整合算子**區塊（含 Swarm 賽局排隊與相干性宣告）以及升格 AI 雙核指標區（AI 信心度 100.0%、σ 方差 0.3125、精確度提升 +58.4% 與微觀/宏觀雙色進度條）。
* 下排平行設置 4 大算子子卡片：
  1. CV 視覺越浪率 (p/min) `#facc15`
  2. MMSI 客輪沉降 (Squat m) `#38bdf8`
  3. FNO 100ms 預報波高 (m) `#ef4444`
  4. 64D 量子拓撲相干性 `#c084fc`

### 2. 左側戰術控制欄 (32% 欄寬) 共 4 張卡片
1. **PINN Engine 即時水文門檻比對**：Hs Pier, W Local, UKC, FB Pier 與 PASS/VETO 徽章。
2. **當日船班官模燈號、時窗與戰略方案總結整合卡片**：官方 vs GEM 燈號、08:30 首班/11:20 止登/14:20 強制撤離細節，並**直接嵌入高光黃【戰略方案總結】**。
3. **⚓ 游擊式動態調度與時窗預判 (`#f59e0b` 邊框)**：靠泊/撤離實體碼頭與上下午時窗預警。
4. **🌀 颱風、雙週長浪與奇門氣場預判專區 (`#a855f7` 邊框)**：中颱/955hPa 動態、250km 暴風半徑、2D 氣壓梯度 (1.10 hPa/km)、東北季風共振、Week 1/2 雙週長浪趨勢、&plusmn;15% 不確定性與奇門 100% 匹配提示。

### 3. 右側動態圖表陣列 (68% 欄寬)
* **2x2 時間線圖表**：Hs (黃虛線 1.20m)、Wind (橘虛線 10.80m/s)、UKC (紅虛線 1.50m)、Tp 週期 (紫虛線 12.0s)，注入 11:00 與 14:00 無箭頭判點虛線。
* **未來七天雙軸趨勢圖**：Hs 與 Wind 雙 Y 軸曲線，懸浮 Tooltip **動態標示各天裁決燈號（🔴/🟡/🟢）與戰術結論**。
* **戰略三方案評估 (Ground Truth Comparison)**：方案 A、B、C 據值對比（方案 C 採高光黃 `#facc15`）。

---

## 四、 手持端 (`mobile.html`) 輕量化 100% 垂直單欄流規範

**嚴禁加載 ECharts DOM**，卡片依序為：
1. 頂部連線狀態卡片 (`● LIVE SSOT`)。
2. Watchdog 數據過期 Banner (`#staleAlertMob`)。
3. Q-Mode 戰術裁決 Banner (`#vetoBannerMob`)。
4. AI 雙核相對精確度與注意力閘卡片。
5. PINN 物理水文邊界卡片 (2x2 網格)。
6. **當日船班官模燈號、時窗與未來 3 天開/封島預測卡片**：包含 08:30/11:20/14:20 船班細節與 D+1 (🔴 封島), D+2 (🟡 限制靠泊), D+3 (🟢 全線開放) 預測模組。
7. ⚓ 游擊式動態調度處置卡片 (`#f59e0b` 邊框)。
8. 🌀 颱風與奇門氣場預判卡片 (`#a855f7` 邊框)。
9. 🚀 Level 5 邊緣高維算子卡片 (`#10b981` 邊框，2x2 網格)。
10. **戰略三方案評估與標籤檢核卡片 (Ground Truth)**：帶有浪高/風速數據據值、PASS/RESTR/VETO 檢核標籤與戰略總結。
11. 裝置視角切換導覽列。

---

## 五、 SSOT JSON Schema 最高標準 (v36D.13.0 Complete)

```json
{
  "version": "v36D.13.0 Level 5 Complete",
  "timestamp": "2026-09-13 12:00:00 CST",
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
      "dynamic_squat_m": 0.82,
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
### 日後維運與對話 SOP 指南

未來進行任何系統微調或需求更動時，發送以下 Prompt 模板即可：

> **【GEM-V36D 專案維護指令】**
> 
> **1. 最高雙柱原則**：嚴格遵守 `GEM_SPEC_MASTER.md` 的「版面幾何固定 (CLS = 0)」與「數據單向更新化 (Data-Only SSOT)」。絕不改動 HTML/CSS 幾何骨架，前端僅透過 `textContent` 靜態對接 `latest_decision.json`。
> **2. 對接規範版本**：`v36D.13.0 Level 5 Complete`（包含置頂列整合、圖表虛線警戒線、無箭頭判點虛線、手持端 3 天預測與 Ground Truth 據值標籤）。
> **3. 本次修改需求**：[在此填入您想調整的細節，例如：請將 main_orchestrator.py 內的颱風氣壓梯度計算公式改為以遙測陣列為準]
> **4. 輸出要求**：僅輸出修改後的受影響檔案完整程式碼。
