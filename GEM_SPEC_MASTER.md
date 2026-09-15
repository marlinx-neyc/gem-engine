GEM_SPEC_MASTER.md (v36D.130.0 Full Tactical Matrix Master) 全域規範本規範為 GEM-V36D 龜山島數位雙生海事戰術控制台（包含 Desktop 端、Mobile 端、Python 後端算子與 GitHub Actions CI/CD 排程）之最高技術標準。全系統維運與程式碼變更必須 100% 恪守「版面幾何固定化 (CLS = 0)」與「數據單向更新化 (Data-Only SSOT)」雙柱原則。一、 核心系統哲學與綠燈放行機制 (Core Pillars & Green Pass Standard)1. 版面固定化原則 (Layout Lockdown / CLS = 0)CSS Containment 座標鎖定：全視角 HTML 元件（desktop.html、mobile.html）容器與卡片實體設定 contain: strict 或 contain: content 屬性，徹底隔絕 DOM 幾何重排。Zero-Reflow 純文字節點寫入：前端 JavaScript 更新時僅允許使用 node.textContent 替換純數據文字與動態切換 Style 燈號顏色（紅/黃/綠），嚴禁使用 innerHTML 重新拼接或增刪 DOM 節點。零版面位移 (CLS = 0)：卡片高度、寬度、Grid 網格與 Margin 間距由 CSS 剛性鎖定，數據長短變更不得引發版面伸縮。2. 端側雙時鐘與綠燈放行歸段 (Green Pass Standard)端側實時秒針時鐘：前端獨立計時器實時格式化顯示 Asia/Taipei (UTC+8) 當前時間（即時：YYYY/MM/DD HH:mm:ss CST）。綠燈放行歸段 (Green Pass Standard)：正式遙測正常：API 響應正常且未觸發 VETO 時，輸出 🟢 100.0% [完整同化 PASS] 與 🟢 放行靠泊。備援演算正常：遙測 API 斷流但奇門與模型備援推算順暢且水文指標安全時，輸出 🟢 85.0% [奇門與模型備援 PASS] 與 🟢 放行靠泊，絕不懸掛紅色過期阻斷 Banner。雙重硬阻斷 (Hard VETO Only)：僅於「遙測與備援模型雙重斷流且時間差 $> 30\text{秒}$」時掛載 🔴 數據過期 (READ_ONLY_BACKUP)，或「實體觸發六重物理極值」時掛載 🔴 物理VETO觸發 警示 Banner。二、 雙端 DOM 幾何佈局規格 (35% / 65% CLS = 0 Geometry)CSS/* 頂、左、右雙欄剛性幾何鎖定 (CLS = 0) */
.dashboard-header-master { width: 100%; height: 120px; contain: strict; }
.dashboard-main-layout { display: flex; gap: 20px; width: 100%; }
.layout-left-tactical  { flex: 0 0 35%; max-width: 35%; contain: content; }
.layout-right-charts   { flex: 0 0 65%; max-width: 65%; contain: content; }
1. 桌面端 (desktop.html) 左欄 4 卡片與右欄架構頂部一體化主卡片 (100% 橫向全寬，高度 120px)：鎖定 LIVE SSOT 呼吸燈、CST 秒針時鐘與 Level 5 邊緣算子 4 格微型網格（CV 越浪率、MMSI 沉降、FNO 100ms 預報、64D 量子拓撲）。左欄戰術控制區 (35% 欄寬，包含 4 張獨立卡片)：Card 1 (1. PINN Engine 即時水文門檻比對)：碼頭波高 (Hs Pier)：3.71 m | VETO (>1.20m)區域風速 (W Local)：8.50 m/s | PASS (<=10.80m/s)富餘水深 (UKC)：5.84 m | PASS (>=1.50m)預留乾舷 (FB Pier)：2.00 m | PASS (>=0.50m)動態潮位 Eta (1.20 m) 與自適應 Alpha (0.95) 標註。Card 2 (2. 當日預警時窗與戰略總結)：海象標準：Hs <= 1.20m | W <= 10.80m/s | Δθ < 45°10:50 預警簡訊：預警演練（提早 0.5h 準備止登）11:20 止登時窗：軟性封島（切換至【南岸權宜碼頭】）13:50 預警簡訊：預警演練（提早 0.5h 準備清島）14:20 強制撤離：從【南岸權宜碼頭】全船撤離【烏石港】高光戰術總結：執行「10:50/13:50 雙預警，11:20 止登【南岸碼頭】，14:20 全員撤離至【烏石港】」Card 3 (3. ⚓ 游擊式動態調度與時窗預判 - 黃框)：登島靠泊碼頭：【南岸權宜碼頭】應急撤離碼頭：【南岸權宜碼頭】 -> 返航【烏石港】T-30 / T-45 / T-60 預警向量狀態列（T-60 氣場、T-45 湧浪陡升、T-30 移防）。Card 4 (4. 🌀 颱風、長浪、南北角水動力與天文潮專區 - 紫框)：【北岸碼頭區域】：風速/向 12.2 m/s (045° NE) VETO | 浪高 3.95 m VETO | 流速/向 1.8 kts (030° NNE) WARN【南岸碼頭區域】：風速/向 8.5 m/s (065° ENE) PASS | 浪高 3.71 m VETO | 流速/向 0.9 kts (110° ESE) PASS龜首崩塌風險：0.15 | 奇門匹配率：85.00%天文潮影響：農曆 08/04-08/10 朔望大潮 1.80m，乾潮自動扣減 UKC 0.45m，滿潮自動扣減乾舷 FB 1.35m。右欄圖表與評估陣列 (65% 欄寬)：上層 (2x2 時間線預測矩陣)：含 11:20 止登 與 14:20 撤離 無箭頭虛線切分標註及門檻虛線（Hs 1.20m、Wind 10.80m/s、UKC 1.50m、Tp 12.0s）。中層 (未來 7 天雙軸趨勢圖)：Hs 與 Wind 雙 Y 軸折線/柱狀圖，Hover Tooltip 彈出當日戰術裁決。下層 (Ground Truth 三方案評估比對表格)：完整渲染方案 A、方案 B 與方案 C 對比表格，方案 C 實施高光標註。2. 手持端 (mobile.html) 輕量化垂直單欄流嚴禁加載 ECharts DOM，卡片依序為：置頂雙時鐘卡片、Watchdog Banner、1. PINN 水文極值、2. 預警時窗與戰略總結、3. ⚓ 游擊調度卡片、4. 🌀 颱風水動力與 Level 5 算子卡片。  三、 T-30/T-45/T-60 超前預警與奇門 70% RL 門控矩陣  預警等級 / 時窗觸發指標與算子戰術指令與處置綠燈/熔斷狀態T - 60 min (氣場預警)奇門巽宮/艮宮同化匹配率 $\ge 70\%$解鎖 Attention Gate (Macro Bias 0.40)，推播氣場預警與客流管制🟢 常規預警 (綠燈可靠泊)T - 45 min (海象預警)浪高陡升 $dH_s/dt > 0.05\text{ m/10min}$ 或長浪 $T_p > 12.0\text{ s}$發布 🟡 海象陡升預警，動態壓縮止登時間 $T_{\text{stop}}$🟡 限制靠泊 (動態提示)T - 30 min (移防預警)風向偏轉 $\Delta\theta \ge 45^\circ$ 側風預警北岸屏障失效，提前 30 分鐘指引切換 【南岸權宜碼頭】 靠泊🟢 游擊放行 (綠燈靠泊)T - 0 min (剛性熔斷)觸發任一 PINN 剛性否決極值切換為 【防颱避風/禁止靠泊】，強制返航 【烏石港】🔴 剛性熔斷 (紅燈阻斷)四、 全海象六重剛性 VETO 熔斷與動態水文算子1. 動態水文幾何演算 (非硬編碼)前端與後端嚴禁寫死固定數值，必須結合實測潮位 $\eta_{\text{tide}}$ 與雙體客輪 Squat 沉降量（$S_{\text{quat}} = 0.82\text{ m}$）進行實時解算：$$\text{UKC} = \text{Depth}_{\text{multibeam}} + \eta_{\text{tide}} - D_{\text{draft}} - S_{\text{quat}}$$$$\text{FB}_{\text{pier}} = 3.20\text{ m} - \eta_{\text{tide}}$$2. 六重 PINN 剛性熔斷檢核任一指標觸發即無條件判定 hard_veto_alert: true 且發布 🔴 封島/防颱：碼頭波高：$H_s > 1.20 \cdot \alpha_{\text{adaptive}}\text{ m}$攻角有效風速：$W_{\text{eff}} = W_{\text{local}} \cdot \vert\cos(\Delta\theta)\vert \ge 10.80 \cdot \alpha_{\text{adaptive}}\text{ m/s}$動態富餘水深：$\text{UKC} < 1.50\text{ m}$預留碼頭乾舷：$\text{FB}_{\text{pier}} < 0.50\text{ m}$長浪港池共振：湧浪週期 $T_p > 12.0\text{ s}$ 且碼頭波高 $H_s > 1.00\text{ m}$ ($K_d = 1.00$ 長浪共振)坡體崩塌風險：ARDSWC 龜首崩塌風險比率 $> 0.60$註：自適應下修係數 $\alpha_{\text{adaptive}} \in [0.75, 1.00]$，由歷史事故智庫與餘弦相似度比對自動導出。五、 後端 MLOps、持久化與 SSOT Schema 規範1. Python 後端防爆與訊息差備援算子 (main_orchestrator.py)Safe Float 轉換：使用 safe_float(val, default) 徹底消除 API 回傳 null、None 或 "-99" 引發之 TypeError 崩潰。數值小數精度控制：所有浮點數據寫入 SSOT JSON 前統一執行 round(x, 2)，前端 UI 渲染時統一套用 .toFixed(2) 格式化。訊息差奇門推算算子：當遙測 API 斷流（$T_{\text{stale}} > 30\text{ s}$）時，自動啟動奇門 64D 拓撲與歷史事故圖譜進行訊息差補算，並緊縮 5% 自適應門檻（$\alpha \times 0.95$）進行安全保險。Auto-Gate 沙盒演練與 .pt 持久化：影子訓練器（XianHengAutonomousShadowTrainer）擷取殘差進行 LoRA（$Rank=4$）微調，通過 1,000 次 Monte Carlo 沙盒演練（通過率 $\ge 95\%$，險卦違例為 0）後無縫熱替換，並導出覆寫 model_v36D_latest.pt 權重檔。2. 標準 SSOT JSON Payload 規格範例 (latest_decision.json)JSON{
  "version": "v36D.130.0 Full Tactical Matrix Master",
  "timestamp": "2026-09-15 10:52:52 CST",
  "decision": "🔴 封島/防颱",
  "confidence_score": 85.0,
  "confidence_label": "🟢 85.0% [奇門與模型備援 PASS]",
  "hard_veto_alert": true,
  "physics_metrics": {
    "hs_pier_m": 3.71,
    "w_local_ms": 8.50,
    "w_effective_ms": 5.23,
    "tide_eta_m": 1.20,
    "s_quat_m": 0.82,
    "ukc_m": 5.84,
    "fb_pier_m": 2.00,
    "slope_landslide_risk": 0.15,
    "adaptive_alpha": 0.95,
    "historical_similarity": 0.92,
    "has_veto": true
  },
  "guerrilla_dispatch": {
    "berthing_pier": "【防颱避風/禁止靠泊】",
    "evacuation_pier": "【強制撤離】 -> 返航【烏石港】",
    "early_warning_vector": {
      "t60_qimen_warning": "🟡 T-60 氣場與颱壓預警：奇門同化匹配率 85.0% >= 70%，已解鎖 64D 拓撲 Attention Gate (Macro Bias 0.40)",
      "t45_wave_steep_warning": "🟡 T-45 湧浪海象預警：長浪週期 Tp=14.5s (>12.0s Kd=1.00 共振穿透) 趨勢預警",
      "t30_pier_shift_warning": "🟡 T-30 移防預警：風向偏轉 (Δθ=52.0° >= 45° 側風) 且橫流 1.8kts，指引切換至【南岸權宜碼頭】"
    },
    "tactical_summary": "⚠️ 三方案定性定量總結：方案A(傳統官方): 僅憑風速 8.5m/s 評估與方案B(氣象署): 缺乏港池越浪、湧浪週期與 Squat 數據預判放行/限縮；方案C(GEM-V36D Ground Truth): 依攻角風速 5.23m/s、湧浪 Kd=1.00 與動態門檻 7.67m/s精確比對全海象歷史智庫(α=0.71)，判定【剛性熔斷】！游擊調度決策：觸發全海象 PINN 剛性否決 (有效風速 5.23m/s, 浪高 3.71m, 湧浪 Tp=14.5s)。建議 11:02 止登，11:47 全員撤離至烏石港。",
    "t_stop_window": "11:02",
    "t_evac_window": "11:47",
    "is_backup_mode": true
  },
  "level5_advanced_metrics": {
    "vision_overtopping_rate_pmin": 1.31,
    "vision_kd_bias": 0.0295,
    "fno_forecast_mean_hs_m": 1.58,
    "quantum_topology_coherence": 0.4682
  },
  "qimen_macro_consensus": {
    "consensus_rate_pct": 85.0,
    "macro_advisory_enabled": true,
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 85.0% (>=70%)，已啟動 Attention Gate 宏觀參研與訊息差備援"
  }
}
