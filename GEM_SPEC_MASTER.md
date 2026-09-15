GEM_SPEC_MASTER.md (v36D.150.0 Integrated Ultimate Specification)
本規範為 GEM-V36D 龜山島數位雙生海事戰術控制台（包含 Desktop 端、Mobile 端、Python 後端算子與 GitHub Actions CI/CD 排程）之最高技術標準。全系統維運與程式碼變更必須 100% 恪守「版面幾何固定化 (CLS = 0)」與「數據單向更新化 (Data-Only SSOT)」雙柱原則。

1. 核心系統哲學與雙端 UI 剛性鎖定 (Core Pillars & UI Standards)
版面固定化原則 (Layout Lockdown / CLS = 0)

CSS Containment 座標鎖定：全視角 HTML 元件（desktop.html、mobile.html）容器與卡片實體設定 contain: strict 或 contain: content 屬性，徹底隔絕 DOM 幾何重排。

Zero-Reflow 純文字節點寫入：前端 JavaScript 更新時僅允許使用 node.textContent 替換純數據文字與動態切換 Style 燈號顏色（紅/黃/綠），嚴禁使用 innerHTML 重新拼接或增刪 DOM 節點。

零版面位移 (CLS = 0)：卡片高度、寬度、Grid 網格與 Margin 間距由 CSS 剛性鎖定，數據長短變更不得引發版面伸縮。

置頂主卡片一體化與指標元件 (Header Master Box - 120px)

藍色心跳連線燈號：包含藍色心跳呼吸燈（#38bdf8），實時記錄通報與心跳計數器。

科學物理與奇門氣場佔比條 (Progress Bar)：以進度條直觀展示微觀物理與奇門氣場之決策權重比（如：微觀物理 65% / 奇門氣場 35%）。

Level 5 微型算子 4 格網格：包含 CV 越浪率 (#facc15)、MMSI 客輪沉降 (#38bdf8)、FNO 100ms 預報波高 (#ef4444) 與 64D 量子拓撲相干性 (#c084fc)。

2. 雙端 DOM 幾何佈局規格 (35% / 65% CLS = 0 Geometry)
CSS
/* 頂、左、右雙欄剛性幾何鎖定 (CLS = 0) */
.dashboard-header-master { width: 100%; height: 120px; contain: strict; }
.dashboard-main-layout { display: flex; gap: 20px; width: 100%; }
.layout-left-tactical  { flex: 0 0 35%; max-width: 35%; contain: content; }
.layout-right-charts   { flex: 0 0 65%; max-width: 65%; contain: content; }
1. 桌面端 (desktop.html) 左欄 4 卡片結構 (35% 欄寬)

Card 1 (1. PINN Engine 即時水文門檻比對)：

碼頭波高 (H 
s
​
  Pier)：3.71 m | VETO (> 1.20 m)

區域風速 (W Local)：8.50 m/s | PASS (<= 10.80 m/s)

富餘水深 (UKC)：5.84 m | PASS (>= 1.50 m)

預留乾舷 (FB Pier)：2.00 m | PASS (>= 0.50 m)

實時標註動態潮位 η 
tide
​
  (1.20 m) 與自適應調值 α 
adaptive
​
  (0.95)。

Card 2 (2. 當日預警時窗與戰略總結 - 含雙端開島決策)：

07:30 當日開島判別：官方/GEM 比對，輸出當日開/封島燈號（🟢 可開島 / 🔴 封島）。

10:50 預警簡訊：預警演練（提早 0.5h 準備止登）。

11:20 止登時窗：軟性封島（切換至【南岸權宜碼頭】）。

13:50 預警簡訊：預警演練（提早 0.5h 準備清島）。

14:20 強制撤離：從【南岸權宜碼頭】全船撤離【烏石港】。

16:30 明日開島預判：官方/GEM 預測，輸出明日開/封島燈號（🟡 限制靠泊 / 🔴 預警封島）。

Card 3 (3. ⚓ 游擊式動態調度與時窗預判 - 黃框)：

登島靠泊與應急撤離碼頭指引。

T-30 / T-45 / T-60 超前預警向量狀態列（T-60 氣場、T-45 湧浪陡升、T-30 移防）。

游擊處置決策說明：📌 游擊處置決策：觸發全海象 PINN 剛性否決 (有效風速 5.23m/s, 浪高 3.71m, 湧浪 Tp=14.5s)。建議 11:02 止登，11:47 全員撤離至烏石港。

Card 4 (4. 🌀 颱風、長浪、南北角水動力與天文潮專區 - 紫框)：

北岸與南岸區域水動力矩陣（風速、浪高、流速及流向）。

龜首崩塌風險比率 (0.15)、奇門氣場匹配率 (85.00%)。

天文朔望大潮 1.80 m 扣減說明：乾潮自動扣減 UKC 0.45 m，滿潮自動扣減乾舷 FB 1.35 m。

2. 手持端 (mobile.html) 輕量化垂直單欄流
嚴禁加載 ECharts DOM，卡片依序為：置頂雙時鐘卡片、Watchdog Banner、1. PINN 水文極值、2. 預警時窗與戰略總結、3. ⚓ 游擊調度卡片、4. 🌀 颱風水動力與 Level 5 算子卡片。

3. T-30/T-45/T-60 超前預警與奇門 70% RL 門控矩陣
預警等級 / 時窗	觸發指標與算子	戰術指令與處置	綠燈 / 熔斷狀態
T - 60 min (氣場預警)	奇門巽宮/艮宮同化匹配率 ≥70%	解鎖 Attention Gate (Macro Bias 0.40)，推播氣場預警與客流管制	🟢 常規預警 (綠燈可靠泊)
T - 45 min (海象預警)	浪高陡升 dH 
s
​
 /dt>0.05 m/10min 或長浪 T 
p
​
 >12.0 s	發布 🟡 海象陡升預警，動態壓縮止登時間 T 
stop
​
 	🟡 限制靠泊 (動態提示)
T - 30 min (移防預警)	風向偏轉 Δθ≥45 
∘
  側風	預警北岸屏障失效，提前 30 分鐘指引切換 【南岸權宜碼頭】 靠泊	🟢 游擊放行 (綠燈靠泊)
T - 0 min (剛性熔斷)	觸發任一 PINN 剛性否決極值	切換為 【防颱避風/禁止靠泊】，強制返航 【烏石港】	🔴 剛性熔斷 (紅燈阻斷)
4. 全海象六重 PINN 剛性極值熔斷與水文動態算子
1. 動態水文幾何演算 (非硬編碼)
前端與後端結合實測潮位 η 
tide
​
  與雙體客輪 Squat 沉降量（S 
quat
​
 =0.82 m）實時解算：

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
 =3.20 m−η 
tide
​
 
2. 六重 PINN 剛性熔斷檢核 (任一指標觸發即無條件判定 hard_veto_alert: true)

碼頭波高：H 
s
​
 >1.20⋅α 
adaptive
​
  m

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

動態富餘水深：UKC<1.50 m

預留碼頭乾舷：FB 
pier
​
 <0.50 m

長浪港池共振：湧浪週期 T 
p
​
 >12.0 s 且碼頭波高 H 
s
​
 >1.00 m (K 
d
​
 =1.00 長浪共振)

坡體崩塌風險：ARDSWC 龜首崩塌風險比率 >0.60

註：自適應下修係數 α 
adaptive
​
 ∈[0.75,1.00]，由歷史事故智庫與餘弦相似度比對自動導出。

5. 右欄 ECharts 視覺陣列與 Ground Truth 三方案評估 (65% 欄寬)
2x2 時間線圖表矩陣 (Upper Right)

圖例規範 (Legend)：每張圖表右上角顯示標準圖例。

警戒線與數值標註 (markLine)：

H 
s
​
  碼頭波高：H 
s
​
 =1.20 m 紅色虛線 + 標籤數值。

W 攻角風速：W=10.80 m/s 橘色虛線 + 標籤數值。

UKC 富餘水深：UKC=1.50 m 綠色虛線 + 標籤數值。

T 
p
​
  湧浪週期：T 
p
​
 =12.0 s 紫色虛線 + 標籤數值。

游標 Hover Tooltip：懸浮時顯示當前精確數值與判準燈號（🔴 VETO / 🟡 WARN / 🟢 PASS）。

未來 7 天雙軸趨勢圖 (Middle Right)

網格透明度：設定 splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.15)' } }（50% 透明度）。

雙警戒線：包含 H 
s
​
 =1.20 m 與 W=10.80 m/s 兩條警戒線與數值標籤。

Tooltip 懸浮燈號：懸浮時顯示當日 H 
s
​
 , W 數值與對應戰術裁決燈號。

Ground Truth 三方案評估比對表格 (Lower Right)
完整渲染方案 A、方案 B 與方案 C 對比表格，方案 C（GEM-V36D）實施高光標註並實時顯示防線決策。

6. 後端 MLOps、.pt 持久化與標準 SSOT JSON Schema
1. Python 後端防爆與訊息差備援算子 (main_orchestrator.py)

Safe Float 轉換：使用 safe_float(val, default) 消除 API 回傳 null 或傳輸異常引發之 TypeError 崩潰。

數值小數精度控制：所有浮點數據寫入 SSOT JSON 前統一執行 round(x, 2)，前端 UI 渲染套用 .toFixed(2) 格式化。

訊息差奇門推算算子：當遙測 API 斷流（T 
stale
​
 >30 s）時，啟動奇門 64D 拓撲進行訊息差補算，並緊縮 5% 自適應門檻（α×0.95）進行保險。

Auto-Gate 沙盒演練與 .pt 持久化：影子訓練器（XianHengAutonomousShadowTrainer）擷取殘差進行 LoRA（Rank=4）微調，通過 1,000 次 Monte Carlo 沙盒演練（通過率 ≥95%，險卦違例為 0）後熱替換，並覆寫導出 model_v36D_latest.pt。

2. 標準 SSOT JSON Payload 規格範例 (latest_decision.json)

JSON
{
  "version": "v36D.150.0 Full Tactical Matrix Master",
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
    "tactical_summary": "⚠️ 三方案定性定量總結：方案A(傳統官方): 僅憑風速 8.5m/s 評估與方案B(氣象署): 缺乏港池越浪、湧浪週期與 Squat 數據預判放行/限縮；方案C(GEM-V36D Ground Truth): 依攻角風速 5.23m/s、湧浪 Kd=1.00 與動態門檻 7.67m/s 精確比對全海象歷史智庫(α=0.71)，判定【剛性熔斷】！游擊調度決策：觸發全海象 PINN 剛性否決 (有效風速 5.23m/s, 浪高 3.71m, 湧浪 Tp=14.5s)。建議 11:02 止登，11:47 全員撤離至烏石港。",
    "t_stop_window": "11:02",
    "t_evac_window": "11:47",
    "is_backup_mode": true,
    "open_island_0730": "🔴 封島",
    "open_island_1630_tomorrow": "🔴 預警封島"
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
