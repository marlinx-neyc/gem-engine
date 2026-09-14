GEM-V36D (v36D.16.5 Level 7 Complete Master) 全域 SSOT 代碼自我稽核與開發規範
本規範為 GEM-V36D 龜山島數位雙生海事戰術控制台（包含 Desktop 端、Mobile 端、Python 後端算子與 GitHub Actions CI/CD 自動化排程）之最高技術標準。全系統維運與程式碼變更必須 100% 恪守「版面幾何固定化 (CLS = 0)」與「數據單向更新化 (Data-Only SSOT)」雙柱原則。

一、 系統哲學：雙柱原則與端側抗過期機制 (Core Pillars & Anti-Stale)
1. 版面固定化原則 (Layout Lockdown Specification / CLS = 0)
CSS Containment 座標鎖定：全視角 HTML 元件（desktop.html、mobile.html、index.html）所有卡片與容器必須設定 contain: strict 或 contain: content 樣式屬性，徹底隔絕 DOM 幾何重排與重繪。

Zero-Reflow 純文字節點寫入：前端 JavaScript 在進行 5 秒定時數據更新時，僅允許使用 node.textContent 替換純數據文字與動態切換既有 Style 顏色（如綠/黃/紅燈號），絕對禁止使用 innerHTML 重新拼接或動態增刪 DOM 節點。

永久零版面位移 (CLS = 0)：卡片高度、寬度、Grid 網格與 Margin 間距於 CSS 中實體鎖定，數據長短變更不得引發任何元件尺寸伸縮或累積版面位移。

2. 端側 Asia/Taipei CST 動態雙時鐘與 30 秒抗過期 Watchdog
端側實時動態時鐘：前端頁面建立獨立 1 秒計時器，透過 Asia/Taipei (UTC+8) 實時格式化顯示當前時間（即時：YYYY/MM/DD HH:mm:ss CST），確保桌面與手機端秒針穩定躍動。

SSOT 數據時間驗證：讀取 latest_decision.json 之 timestamp 欄位（格式：YYYY-MM-DD HH:mm:ss CST）。

30 秒抗過期硬阻斷 (Anti-Stale Watchdog)：前端比對 Math.abs(Date.now() - ssotTimestamp)，若時間差 >30 秒或後端回傳 hard_veto_alert: true，自動於頂部掛載 🔴 數據過期 (READ_ONLY_BACKUP) 或 🔴 物理VETO觸發 警示，防止指揮官依據舊數據做靠泊決策。

二、 全域 UI 視覺、圖表互動與色彩對齊規範 (Global UI & Styling)
採用暗色科技風 (Dark Tech) 佈局，色彩、圖表互動與警戒線規範實施 100% 剛性對齊：

水文/氣象指標	主配色 (Hex)	警戒/門檻線規格	門檻條標與燈號對齊
Hs 碼頭波高	警戒紅 (#ef4444)	Hs 1.20m 虛線 (type: 'dashed')	>1.20m⟹🔴 VETO
Wind 局部風速	警戒橘 (#f59e0b)	Wind 10.80m/s 虛線 (type: 'dashed')	>10.80m/s⟹🔴 VETO
UKC 富餘水深	安全綠 (#10b981)	UKC 1.50m 虛線 (type: 'dashed')	<1.50m⟹🔴 VETO
Tp 浪週期	紫光 (#c084fc)	Tp 12.0s 虛線 (type: 'dashed')	>12.0s⟹🟣 WARN (長浪)
1. 2x2 時間線圖表矩陣規範 (desktop.html)
懸浮燈號 Tooltip：游移至點位時，Tooltip 自動彈出並解析當前時間點燈號徽章（🔴 VETO / 🟡 WARN / 🟢 PASS）。

無箭頭判點虛線：11:20 止登與 14:20 撤離之垂直時間虛線必須關閉端點箭頭 (symbol: 'none')，且虛線顏色與該圖折線 100% 匹配。

警戒線與數值整合：警戒虛線右側必須標註明確文字標籤（例如：Hs 1.20m 警戒線），顏色與折線一致。

完整圖例顯示 (Legend)：4 張圖表頂部右上角均必須包含標準 ECharts 圖例。

2. 未來七天雙軸趨勢圖規範
隱藏折線重複文字：設定 label: { show: false }，消除畫面上密密麻麻的疊加數字。

游標動態裁決 Tooltip：當游標懸浮（Hover）至點位時，彈出視窗精確顯示當日戰術裁決（🔴 剛性封島 / 🟡 限制靠泊 / 🟢 全線開放）與 Hs 1.20m / Wind 10.80m/s 雙警戒線比較。

三、 桌面端 (desktop.html) 頂部一體化與 32% / 68% 剛性雙欄規範
1. 置頂一體化整合主卡片 (header-master-card)
橫向主標題與動態心跳：包含主標題、● LIVE SSOT 呼吸燈，以及動態心跳計數器（通報 48 次 | 心跳 100%）。

Level 5 邊緣算子 4 格網格：

CV 視覺越浪率 (p/min) #facc15

MMSI 客輪沉降 (Squat m) #38bdf8

FNO 100ms 預報波高 (m) #ef4444

64D 量子拓撲相干性 #c084fc

2. 左側戰術控制欄 (32% 欄寬) 共 4 張卡片
PINN Engine 即時水文門檻比對：Hs Pier, W Local, UKC, FB Pier 與 PASS/VETO 徽章。

當日預警時窗與戰略方案總結：包含 08:30 靠泊【南岸權宜碼頭】、10:50/13:50 預警、11:20 止登與 14:20 強制撤離至【烏石港】細節，並嵌入高光黃【戰略方案總結】。

⚓ 游擊式動態調度與時窗預判 (#f59e0b 邊框)：登島靠泊【南岸權宜碼頭】與撤退離島至【烏石港】。

🌀 颱風、長浪、南北角水動力與天文潮專區 (#a855f7 邊框)：

南北角雙區域水動力矩陣：

【北岸碼頭區域】：風向/速 12.2m/s (NE) 🔴 VETO | 浪高 3.95m 🔴 VETO | 流速 1.8kts (NNE) 🟡 RESTR

【南岸碼頭區域】：風向/速 8.5m/s (ENE) 🟢 PASS | 浪高 3.71m 🔴 VETO | 流速 0.9kts (ESE) 🟢 PASS

天文潮 (農曆 M/D) 與潮差影響：標明農曆日期（如 農曆 08/04 - 08/10 朔望大潮），說明滿潮 +1.35m / 乾潮 -0.45m (總潮差 1.80m)；乾潮直接扣減 UKC 水深 0.45m，滿潮直接扣減 碼頭乾舷 (FB Pier) 1.35m，導致越浪風險劇增。

未來 1 個月定性、定量與時間點宏觀趨勢推演：

Week 1 (09/14-09/20, 農曆 08/04~08/10): 定量 Hs 2.5–3.8m、風速 10–14m/s，強東北季風與颱風共振，巽宮長浪穿透率 75% (🔴 高危期)。

Week 2 (09/21-09/27, 農曆 08/11~08/18 朔望大潮): 定量 Hs 1.5–2.2m、風速 7–9m/s，大潮低潮期 UKC 扣減 0.45m (🟡 限制游擊靠泊期)。

Week 3-4 (09/28-10/14, 農曆 08/19~09/05): 秋季季風主導平水期，定量 Hs 0.8–1.1m (🟢 常規開放期)。

3. 右側動態圖表陣列 (68% 欄寬)
2x2 時間線圖表矩陣：Hs、Wind、UKC、Tp 圖表。

未來七天雙軸趨勢圖：Hs 與 Wind 雙 Y 軸曲線。

戰略三方案評估 (Ground Truth Comparison)：對比方案 A（傳統官方）、方案 B（氣象局）與方案 C（GEM-V36D 剛性熔斷），方案 C 列高光標註。

四、 手持端 (mobile.html) 輕量化 100% 垂直單欄流規範
嚴禁加載 ECharts DOM，卡片依序為：

置頂連線狀態與端側動態雙時鐘卡片 (● LIVE SSOT 連線)。

Watchdog 數據過期 Banner (#staleAlertMob)。

Q-Mode 戰術裁決 Banner (#vetoBannerMob)。

AI 雙核相對精確度與注意力閘卡片。

PINN 物理水文邊界卡片 (2x2 網格)。

船班官模燈號、預警時窗與未來 3 天開/封島預測卡片 (D+1 🔴, D+2 🟡, D+3 🟢)。

⚓ 游擊式動態調度處置卡片 (#f59e0b 邊框)。

🌀 颱風、南北角水動力與天文潮預判卡片 (#a855f7 邊框)：含南北角風/浪/流數據與農曆大潮 1.80m 潮差扣減細節。

🚀 Level 5 邊緣高維算子卡片 (#10b981 邊框，2x2 網格)。

戰略三方案評估與標籤檢核卡片 (Ground Truth)。

裝置視角切換導覽列。

五、 後端算子與 CI/CD 無崩潰自癒規範 (Backend Engine & CI/CD)
1. Python 後端防爆算子 (main_orchestrator.py v36D.16.5)
Safe Float / Safe List 安全轉換：

Python
def safe_float(val: Any, default: float) -> float:
    if val is None: return default
    try:
        v = float(val)
        return default if v < -90 else v
    except (ValueError, TypeError): return default
徹底排除 CWA/TDX API 回傳 null、None、"-99" 或 "-" 引發之 TypeError / ValueError 崩潰。

智庫檔案自動初始化：腳本啟動時自動檢查並生成 KB_20260904_ESE_OVERTOPPING.json，防止 Git 找不到檔案引發 pathspec 剛性錯誤。

全域 Exception 當前時間戳保護：遭遇外部 API 斷流時，自動抓取當前 Asia/Taipei CST 時間戳，寫入降級 SSOT JSON，確保數據流與控制台時間不凍結。

多源 API 降級與波浪式漸進同化：

FNO 代理推算先發：主 API 斷流（超時 >2000ms）時，100ms 內由 FNO 離線算子產出代理數據推播至控制台。

波浪式漸進同化：備援資料抵達後，UKF 濾波器以 100ms–500ms 微波浪週期逐步寫入狀態向量，平滑過渡消能參數。

動態信度燈號 Schema：🟢 100.0% [完整同化 PASS]、🟡 85.5% [波浪同化中 WARN]、⚠️ 65.0% [代理推算 DEGRADED]、🔴 0.0% [數據過期 VETO]。

前置 1,000 次 Monte Carlo 沙盒演練：發布 SSOT 前，自動於邊緣環境進行 1,000 次蒙特卡羅與 FNO 預演，若數據過期或觸發 VETO，對強行放行施加 -9999 致命懲罰，強制收斂至動作 a=3 (🔴 封島)。

2. CI/CD 工作流規範 (.github/workflows/gem_cron.yml)
輕量化安裝：採用 CPU 版 PyTorch 輪子 (pip install --extra-index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu) torch)，避免記憶體溢出 (OOM) 與下載超時。

自動提交與 Rebase 衝突消除：選用 stefanzweifel/git-auto-commit-action@v5 搭配 file_pattern: "*.json"、ref: main 與 branch: main，徹底解決 Git Detached HEAD 與 Pathspec 衝突 (Exit Code 128)。

寫入權限授權：必須配置 permissions: contents: write 與 GitHub Repository Settings 中的 Read and write permissions。

六、 SSOT JSON Schema 最高標準 (v36D.16.5 Complete)
JSON
{
  "version": "v36D.16.5 Zero-Crash Master Complete",
  "timestamp": "2026-09-14 17:00:00 CST",
  "decision": "🔴 封島/防颱",
  "confidence_score": 100.0,
  "confidence_label": "🟢 100.0% [完整同化 PASS]",
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
    "berthing_pier": "【南岸權宜碼頭】",
    "evacuation_pier": "【南岸權宜碼頭】 &rarr; 返航【烏石港】",
    "guerrilla_mode": "BOTH_PIERS_DISABLED",
    "morning_tactic": "⚠️ 上午游擊調撥：北岸越浪，08:30 班次改至【南岸權宜碼頭】靠泊",
    "afternoon_tactic": "🚨 下午游擊撤退：10:50/13:50 雙預警，11:20 止登，14:20 全員撤離至【烏石港】",
    "tactical_summary": "執行「10:50/13:50 雙預警，11:20 止登【南岸碼頭】，14:20 全員撤離至【烏石港】」"
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
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 100.0% (>=70%)，已啟動宏觀參研決策與預警提示"
  }
}
七、 GEM-V36D 專案維護與修復指令模板
未來進行任何系統微調或需求更動時，使用以下 Prompt 模板：

【GEM-V36D 專案維護指令】

1. 最高雙柱與抗過期原則：嚴格遵守 GEM_SPEC_MASTER.md 的「版面幾何固定 (CLS = 0)」、「數據單向更新 (Data-Only SSOT)」與「Asia/Taipei 30 秒 Watchdog 過期防衛」。絕不改動 HTML/CSS 幾何骨架，前端僅透過 textContent 靜態對接 latest_decision.json。
2. 對接規範版本：v36D.16.5 Level 7 Complete Master（含南北角水動力矩陣、天文潮差扣減影響、懸浮燈號 Tooltip、七天趨勢圖隱藏實體數字、心跳連線計數與 CI/CD 零崩潰自癒機制）。
3. 本次修改需求：[在此填入您想調整的細節，例如：請更新 desktop.html 內的預警廣播時間為 10:45]
4. 輸出要求：僅輸出修改後的受影響檔案完整程式碼。比對、分析、優化、整合成一版
