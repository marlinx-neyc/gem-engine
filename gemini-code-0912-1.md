# GEM-V36D 數位雙生海事戰術智庫 — 全域 SSOT 代碼自我稽核與開發規範 (v36D.12.1)

本規範為 GEM-V36D (v36D.12.1) 精簡升級版數位雙生海事戰術控制台（包含 Desktop、Mobile、Master 端與後端 AI 智庫）之最高代碼標準。本版本融合了「游擊式動態調度（上下午時窗管制）」與「奇門 70% 宏觀參研門控」，專注於物理遙測、PINN 剛性防線、游擊移防與 Ground Truth 三方案評估。

---

## 一、 系統哲學與數據解耦原則 (Philosophy & Architecture)

1. **數據與 UI 完全解耦**：AI 運算引擎（Python/Colab/GitHub Actions）純粹作為數據生產者，輸出標準 SSOT `latest_decision.json`；前端網頁（`index.html`、`desktop.html`、`mobile.html`）純粹作為視覺渲染器，嚴禁在前端寫死業務邏輯。
2. **單一真實數據源 (SSOT Consensus)**：全站數據門檻與裁決指標，徹底以 JSON 資料為準，確保雙端顯示完全一致。

---

## 二、 全域 UI 視覺與色彩規範 (Global UI & Color Palette)

全站介面統一採用暗色科技風 (Dark Tech) 佈局，視覺元件與色彩定義如下：

* **背景主色 (`#0b1120`)**：全站頁面與外層容器底色。
* **卡片背景 (`#1e293b`) / 深色框線 (`#334155`)**：所有戰術資訊卡片之背景與邊框。
* **戰術藍 (`#38bdf8`)**：專用於區塊標題、卡片邊框高亮、AI 不確定性方差 $\sigma$ 指標與連線狀態點。
* **警戒紅 (`#ef4444`)**：專用於 VETO 觸發（未過關）、VETO 徽章、全線封島標籤與圖表警戒水平線。
* **安全綠 (`#10b981`)**：專用於 Q1 放行狀態、PASS 合格徽章與雙核精確度提升幅度 (+%)。
* **高光黃 (`#facc15`)**：**專用於戰術裁決總結結論、Ground Truth 方案 C 評估結論與關鍵極限數值**。
* **警戒橘 (`#f59e0b`)**：專用於游擊動態調度卡片邊框、風速警戒線與下午預警時窗。
* **中性灰 (`#94a3b8` / `#334155`)**：專用於 11:00 與 16:00 垂直決策時間虛線，以及圖表網格分割線。

---

## 三、 桌面端 (`desktop.html`) 繪圖與佈局規範 (v36D.12.1)

桌面端採用 32% / 68% 剛性雙欄分割佈局：

### 1. 左側戰術控制欄 (32% 欄寬) 剛性卡片順序
1. **AI 雙核相對精確度與注意力閘卡片 (`#38bdf8` 邊框)**：包含 AI 信心指數、不確定性 $\sigma$ 方差、精確度提升幅度，以及微觀/宏觀雙色動態權重進度條。
2. **即時水文與剛性門檻比對卡片 (PINN Engine)**：包含 Hs Pier、Wind Local、UKC、FB Pier 之數值與 PASS/VETO 狀態徽章。
3. **當日船班官模燈號比對與最後判斷卡片**：包含海象數據與標準值對比（如 $H_s \le 1.20\text{m}$, $W \le 10.80\text{m/s}$, $\Delta\theta < 45^\circ$）、官方 vs GEM 判斷與精確時間點戰術動作（延滯登、游擊南移、止登預警、提早退）。
4. **⚓ 游擊式動態調度與時窗預判卡片 (`#f59e0b` 邊框)**：**[新增區塊]** 動態展示建議靠泊碼頭、戰術調度總結、上午時窗告示、下午時窗預警與奇門 70% 參研狀態提示。

### 2. 右側動態圖表陣列 (68% 主畫廊) 繪圖規範
* **容器高度與圖層邊距**：所有圖表容器具備 `min-height: 220px`，右側邊距（`grid.right`）設為 `65~75`，嚴禁警戒線標籤文字被畫布裁切。
* **2x2 圖表矩陣時間線**：11:00 與 16:00 決策虛線標籤置於頂部 (`insideStartTop`)，嚴禁與 X 軸時間刻度重疊。
* **未來七天雙軸趨勢預判圖表**：雙 Y 軸同步注入 $H_s \le 1.20\text{m}$ 與 $\text{Wind} \le 10.80\text{m/s}$ 雙警戒虛線，Hover Tooltip 必須呈現該日之 PASS/VETO 戰術判準。
* **戰略三方案評估 (Ground Truth)**：位於右側底部，評估方案 A、B、C，方案 C 專用高光黃 (`#facc15`)。

---

## 四、 手機端 (`mobile.html`) 輕量化卡片流規範 (v36D.12.1)

採用 100% 垂直單欄卡片流，嚴禁加載 ECharts DOM 以保證弱網極速載入：

### 100% 垂直卡片流堆疊順序 (由上至下)
1. **頂部連線狀態卡片**：包含 `● LIVE SSOT` 動態藍色呼吸燈與連線計數。
2. **Watchdog 數據過期 Banner (`#staleAlertMob`)**：遙測停滯 > 30 秒時自動彈出紅色警示。
3. **Q-Mode 戰術裁決 Banner (`#vetoBannerMob`)**：紅/綠動態底色高亮當前裁決。
4. **AI 雙核相對精確度與注意力閘卡片 (`#38bdf8` 边框)**。
5. **即時海象數值與剛性門檻比對卡片 (PINN Engine)**。
6. **當日船班官模燈號比對與時窗動態處置卡片**：包含實測數據對比標準值與時間點處置。
7. **⚓ 游擊式動態調度與時窗預判卡片 (`#f59e0b` 邊框)**：**[新增區塊]** 動態展示靠泊碼頭、戰術總結與時窗預警。
8. **今日營運時段檢核 (6~9月規範)**：海象整備 (07:30)、首段 (08:30)、區間 (12:30)、末段 (15:30)、預警 (16:30)、截止 (17:30)。
9. **戰略三方案評估卡片 (Ground Truth)**。
10. **裝置視角切換導覽列**。

---

## 五、 遊擊式動態調度與奇門 70% 參研門控機制

### 1. 游擊式時空調撥原則 (Guerrilla Berthing Matrix)
* **上午場（07:30–11:30）**：若北岸越浪但背風屏障有效（$\Delta\theta < 45^\circ$），發動游擊調撥，授權 08:30 班次切換至南岸碼頭，或執行「延滯登」至 10:00 浪平。
* **下午場（12:00–17:30）**：若超前預測午後風向轉為 ESE（$\Delta\theta \ge 45^\circ$）或長浪穿透（$T_p > 12.0\text{s}$），南北岸屏障雙雙失效，強制取消 15:30 末班，發動「提早退」，人員於 14:20 前清島撤離。

### 2. 奇門 70% 宏觀參研門控 (Qimen 70% Macro Advisory Gate)
* 系統自動比對歷史案例庫，當奇門氣場（巽宮風陣、天風長浪）與物理場同化匹配率 $\ge 70\%$ 時，自動啟用 `qimen_macro_consensus` 參研提醒，將奇門預警文字注入前端面板。

---

## 六、 SSOT JSON Schema 規範 (v36D.12.1)

前端 `window.onSSOTDataReceived(data)` 必須完整解析以下全新 Schema 結構：

```json
{
  "version": "v36D.12.1",
  "timestamp": "2026-09-12 18:40:00 CST",
  "decision": "🔴 封島/防颱",
  "confidence_score": 100.0,
  "hard_veto_alert": true,
  "precision_metrics": {
    "converged_sigma": 0.3425,
    "precision_gain_pct": 52.9
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
    "berthing_pier": "無 (南北岸雙岸屏障失效 / 長浪共振)",
    "guerrilla_mode": "BOTH_PIERS_DISABLED",
    "morning_tactic": "無 (時窗正常)",
    "afternoon_tactic": "🚨 下午游擊撤退：預測午後 ESE 巽宮風陣/長浪，取消 15:30 末班，全員於 14:20 提早撤離",
    "tactical_summary": "執行「下午游擊撤退 / 提早退」"
  },
  "qimen_macro_consensus": {
    "consensus_rate_pct": 100.0,
    "macro_advisory_enabled": true,
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 100.0% (>=70%)，已啟動宏觀參研決策與預警提示"
  }
}