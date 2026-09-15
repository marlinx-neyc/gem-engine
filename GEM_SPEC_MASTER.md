GEM_SPEC_MASTER.md (v36D.100.0 Ultimate Geometry & Qimen RL Master) 全域規範
本規範為 GEM-V36D 龜山島數位雙生海事戰術控制台（Desktop 端、Mobile 端、Python 後端算子與 GitHub Actions CI/CD 排程）之最高技術標準。全系統維運與代碼變更必須 100% 恪守「版面幾何固定化 (CLS = 0)」與「數據單向更新化 (Data-Only SSOT)」雙柱原則。  
MD

一、 核心系統哲學與端側抗過期機制 (Core Pillars & Anti-Stale)
1. 版面固定化原則 (Layout Lockdown / CLS = 0)
CSS Containment 座標鎖定：全視角 HTML 元件（desktop.html、mobile.html、index.html）之所有容器與卡片實體設定 contain: strict 或 contain: content 屬性，徹底隔絕 DOM 幾何重排與重繪。  
MD

Zero-Reflow 純文字節點寫入：前端 JavaScript 於 5 秒定時更新時，僅允許使用 node.textContent 替換純數據文字與動態切換 Style 燈號顏色（紅/黃/綠），嚴禁使用 innerHTML 重新拼接或增刪 DOM 節點。  
MD

零版面位移 (CLS = 0)：卡片高度、寬度、Grid 網格與 Margin 間距由 CSS 剛性鎖定，數據長短變更不得引發版面尺寸伸縮。  
MD

2. 端側 Asia/Taipei CST 雙時鐘與 30 秒 Watchdog
端側實時秒針時鐘：前端建立獨立 1 秒計時器，顯示 Asia/Taipei (UTC+8) 當前時間（即時：YYYY/MM/DD HH:mm:ss CST）。  
MD

30 秒抗過期硬阻斷 (Anti-Stale Watchdog)：比對 latest_decision.json 之 timestamp 時間差 Math.abs(Date.now() - ssotTimestamp)。若時間差 >30秒 或 hard_veto_alert: true，自動於頂部掛載 🔴 數據過期 (READ_ONLY_BACKUP) 或 🔴 物理VETO觸發 警示 Banner，強制阻斷靠泊決策。  
MD
+ 1

二、 雙端 DOM 幾何佈局規格 (35% / 65% CLS = 0 Geometry)
1. 桌面端 (desktop.html) 三區塊剛性幾何配比
CSS
/* 頂、左、右雙欄剛性幾何鎖定 (CLS = 0) */
.dashboard-header-master { width: 100%; height: 120px; contain: strict; }
.dashboard-main-layout { display: flex; gap: 20px; width: 100%; }
.layout-left-tactical  { flex: 0 0 35%; max-width: 35%; contain: content; }
.layout-right-charts   { flex: 0 0 65%; max-width: 65%; contain: content; }
頂部置頂主卡片 (100% 橫向全寬，高度 120px)

  
MD

左側：主標題、● LIVE SSOT 呼吸燈、CST 動態秒針時鐘。  
MD

右側：Level 5 邊緣算子 4 格網格（CV 越浪率、MMSI 沉降、FNO 100ms 預報、64D 量子拓撲）。  
MD

左欄戰術控制區 (35% 欄寬，由 32% 微調升級)

Card 1 (PINN 即時水文與風速)：Hs Pier、W Local、W_eff、UKC、FB Pier 與 PASS/VETO 徽章。  
MD

Card 2 (⚓ 游擊調度與超前預警矩陣)：靠泊/撤離指引、T-30/45/60 預警向量、動態時窗與三方案定性定量總結。  
MD

Card 3 (🌀 颱風水動力與崩塌風險)：南北角水動力矩陣、農曆朔望大潮 1.80m 潮差扣減細節與奇門同化匹配率。  
MD

右欄圖表與評估陣列 (65% 欄寬)

  
MD

上層：2x2 時間線圖表矩陣（Hs, Wind, UKC, Tp）。  
MD

中層：未來 7 天雙軸趨勢圖（隱藏重複實體數字，Tooltip 懸浮燈號）。  
MD

下層：戰略三方案評估表格（Ground Truth 比對，方案 C 高光標註）。  
MD

2. 手持端 (mobile.html) 輕量化垂直單欄流
嚴禁加載 ECharts DOM，卡片依序為：置頂雙時鐘卡片、Watchdog Banner、PINN 水文網格、開/封島預測、⚓ 游擊調度卡片、🌀 颱風水動力卡片、Level 5 高維算子與 Ground Truth 比對表格。  
MD

三、 T-30/T-45/T-60 超前預警與奇門 70% RL 門控矩陣
預警等級 / 時窗	趨勢算子與觸發指標	轉區處置與戰術指令	奇門 70% RL 閉環處置
T - 60 min (氣場預警)	奇門巽宮/艮宮氣場與颱壓同化匹配率 ≥70%	啟動宏觀預警推播，指示備援船隻整備與客流管制	解鎖 64D 量子拓撲 Attention Gate，Macro Bias 權重自 0.15 提升至 0.40
T - 45 min (海象預警)	浪高陡升變率 dH 
s
​
 /dt>0.05m/10min 或長浪 T 
p
​
 >12.0s	發布 🟡 浪高陡升預警，動態壓縮止登時間 T 
stop
​
 	長浪抵達時啟動 K 
d
​
 =1.00 無損穿透算子
T - 30 min (移防預警)	風向夾角變率 dΔθ/dt≥15 
∘
 /10min 且 Δθ≥45 
∘
  側風	預警北岸背風屏障失效，提前 30 分鐘指引移防 【南岸權宜碼頭】	成功引導移防給予 +100 戰術獎勵；訊息差備援吻合給予 +50 獎勵
T - 0 min (剛性熔斷)	觸發任一 PINN 剛性否決門檻	啟動 🔴 剛性熔斷，切換為 【防颱避風/禁止靠泊】，強制返航 【烏石港】	險卦誤報靠泊給予 −9999 致命懲罰，強行收斂至封島動作
四、 全海象六重剛性 VETO 熔斷與動態水文算子
1. 動態水文幾何演算 (非硬編碼)
前端與後端嚴禁使用硬編碼寫死 UKC 與 FB Pier 數值，必須根據實測與雙體客輪 Squat 沉降量（S 
quat
​
 =0.82m）進行實時動態解算：
  
MD

UKC=Depth 
multibeam
​
 +η 
tide
​
 −D 
draft
​
 −S 
quat
​
 
FB 
pier
​
 =3.20m−η 
tide
​
 
2. 六重 PINN 剛性熔斷檢核
任一指標觸發即無條件判定 hard_veto_alert: true 且發布 🔴 封島/防颱：  
MD

碼頭波高：H 
s
​
 >1.20⋅α 
adaptive
​
  m

  
MD

攻角有效風速：W 
eff
​
 =W 
local
​
 ⋅∣cos(Δθ)∣≥10.80⋅α 
adaptive
​
  m/s

  
MD

動態富餘水深：UKC<1.50 m

  
MD

預留碼頭乾舷：FB 
pier
​
 <0.50 m

  
MD

長浪港池共振：湧浪週期 T 
p
​
 >12.0s 且碼頭波高 H 
s
​
 >1.00m（K 
d
​
 =1.00 無損穿透）

坡體崩塌風險：ARDSWC 龜首崩塌風險比率 >0.60

  
MD

註：自適應下修係數 α 
adaptive
​
 ∈[0.75,1.00]，由歷史事故智庫與餘弦相似度比對自動導出。  
MD

五、 後端 MLOps、持久化與 SSOT Schema 規範
1. Python 後端防爆與訊息差備援算子 (main_orchestrator.py)
Safe Float 轉換：使用 safe_float(val, default) 徹底消除 API 回傳 null、None 或 "-99" 引發之 TypeError 崩潰。  
MD

訊息差奇門推算算子：當遙測 API 斷流（T 
stale
​
 >30s）時，自動啟動奇門 64D 拓撲與歷史事故圖譜進行訊息差補算，並緊縮 5% 自適應門檻（α×0.95）進行保險。  
MD

Auto-Gate 沙盒演練與 .pt 持久化：影子訓練器（XianHengAutonomousShadowTrainer）擷取殘差進行 LoRA（Rank=4）微調，通過 1,000 次 Monte Carlo 沙盒演練（通過率 ≥95%，險卦違例為 0）後無縫熱替換，並導出覆寫 model_v36D_latest.pt 權重檔。  
MD

2. 標準 SSOT JSON Payload (latest_decision.json)
JSON
{
  "version": "v36D.100.0 Ultimate Geometry Master",
  "timestamp": "2026-09-15 10:00:00 CST",
  "decision": "🔴 封島/防颱",
  "confidence_score": 100.0,
  "confidence_label": "🟢 100.0% [完整同化 PASS]",
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
    "adaptive_alpha": 0.85,
    "historical_similarity": 0.92,
    "has_veto": true
  },
  "guerrilla_dispatch": {
    "berthing_pier": "【防颱避風/禁止靠泊】",
    "evacuation_pier": "【強制撤離】 -> 返航【烏石港】",
    "early_warning_vector": {
      "t60_qimen_warning": "🟡 T-60 氣場預警：奇門同化匹配率 100.0% >= 70%，已解鎖 64D 拓撲 Attention Gate (Macro Bias 0.40)",
      "t45_wave_steep_warning": "🟡 T-45 湧浪海象預警：長浪週期 Tp=14.5s (>12.0s Kd=1.00 共振穿透) 趨勢預警",
      "t30_pier_shift_warning": "🟡 T-30 移防預警：風向偏轉 (Δθ=52.0° >= 45° 側風)，指引切換至【南岸權宜碼頭】"
    },
    "tactical_summary": "⚠️ 三方案定性定量總結：方案A與方案B預判放行；方案C精確比對歷史智庫(α=0.85)，判定【剛性熔斷】！",
    "t_stop_window": "11:20",
    "t_evac_window": "12:05",
    "is_backup_mode": false
  },
  "level5_advanced_metrics": {
    "vision_overtopping_rate_pmin": 1.31,
    "vision_kd_bias": 0.0295,
    "fno_forecast_mean_hs_m": 1.58,
    "quantum_topology_coherence": 0.4682
  },
  "qimen_macro_consensus": {
    "consensus_rate_pct": 100.0,
    "macro_advisory_enabled": true,
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 100.0% (>=70%)，已啟動 Attention Gate 宏觀參研與 T-60 預警推播"
  }
}
