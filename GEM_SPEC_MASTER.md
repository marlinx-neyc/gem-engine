GEM_SPEC_MASTER.md (v36D.200.0 Qimen Unblind & Official Closure RL Master)本規範為 GEM-V36D 龜山島數位雙生海事戰術控制台（包含 Desktop 端、Mobile 端、Python 後端算子與 GitHub Actions 排程）之最高技術標準[cite: 6, 7]。全系統維運與程式碼變更必須 100% 恪守「版面幾何固定化 ($CLS = 0$)」與「數據單向更新化 (Data-Only SSOT)」雙柱原則。  一、 核心哲學與雙柱原則 (Core Pillars)1. 版面固定化原則 (Layout Lockdown / CLS = 0)CSS Containment 座標鎖定：全視角 HTML 元件（desktop.html、mobile.html）所有卡片與容器實體設定 contain: strict 或 contain: content 屬性，徹底隔絕 DOM 幾何重排。  Zero-Reflow 純文字節點寫入：前端更新時僅允許使用 node.textContent 替換純數據文字與 Style 燈號顏色（紅/黃/綠），嚴禁使用 innerHTML 重新拼接或增刪 DOM 節點。  數字防震與幾何凍結：卡片寬高與 Grid 網格由 CSS 剛性鎖定，數字動態增減套用 font-variant-numeric: tabular-nums，杜絕版面伸縮微震。  2. 數據單向更新化原則 (Data-Only SSOT)後端純數據生產者：後端 AI 算子（master_engine.py）、Colab 訓練腳本與 GitHub Actions 定時工作流，純粹作為數據生產者，僅對接產出、Commit 並 Push 標準 SSOT 檔 latest_decision.json 至 marlinx-neyc/gem-engine 儲存庫[cite: 5, 6, 7]。後端嚴禁覆蓋或生成任何 .html 檔案。  前端純數據渲染器：前端頁面純粹透過 Fetch 靜態輪詢 latest_decision.json，強制追加時間戳記（latest_decision.json?_t=${Date.now()}）並設定 cache: 'no-store'，繞過手持端 PWA 與瀏覽器快取。  二、 剛性四層/七重物理防線與水動力算子矩陣 (Hard VETO Matrix)本系統採納一票否決（Hard VETO）熔斷原則，任何單項算子觸發超標，總體裁決無條件硬阻斷為 🔴 封島/防颱（Q4）[cite: 6, 7]：$$\text{Hard\_Veto} = \text{Veto}_{Hs} \lor \text{Veto}_{W} \lor \text{Veto}_{UKC} \lor \text{Veto}_{FB} \lor \text{Veto}_{Swell} \lor \text{Veto}_{Slope} \lor \text{Veto}_{Official}$$防線維度剛性安全門檻物理算子精算公式剛性熔斷條件與實測對齊1. 碼頭波高 ($H_{s,pier}$)$\le 1.20 \cdot \alpha_{\text{adaptive}}\text{ m}$[cite: 6, 7]$H_{s,pier} = H_{s,CWA} \cdot K_d(T_p) + PINN_{offset}$[cite: 6, 7]$3.71\text{ m}$ [🔴 VETO]。長浪 $T_p = 15.5\text{ s} > 10.0\text{ s}$ 覆寫 $K_d = 1.00$ 港池共振穿透[cite: 5, 6, 7]。2. 攻角風速 ($W_{eff}$)$\le 10.80 \cdot \alpha_{\text{adaptive}}\text{ m/s}$[cite: 6, 7]$W_{eff} = W_{local} \cdot \Vert{}\cos(\Delta\theta)\Vert{} \cdot K_w$[cite: 6, 7]$5.98\text{ m/s}$（局域 $8.50\text{ m/s}$）[🟢 PASS]。未超越剛性極限門檻[cite: 5, 6, 7]。3. 富餘水深 ($UKC$)$\ge 1.50\text{ m}$[cite: 6, 7]$UKC = (d_{chart} + \eta_{tide}) - (d_{draft} + Squat) - H_{s,pier}$[cite: 6, 7]$0.27\text{ m}$ [🔴 VETO]。扣除雙體船蹲沉 $Squat = 0.82\text{ m}$ 及波高位移後水深不足[cite: 5, 6, 7]。4. 預留乾舷 ($FB_{pier}$)$\ge 0.50\text{ m}$[cite: 6, 7]$FB_{pier} = \min(2.00 - \eta_{tide}, 0.15 \text{ if Overtopping} > 0)$[cite: 6, 7]$0.15\text{ m}$ [🔴 VETO]。Vision-PINN 偵測越浪 ($1.31\text{ p/min}$)，乾舷防線硬覆寫失守[cite: 5, 6, 7]。5. 遠洋長浪共振$T_p \le 10.0\text{ s}$  $FNO_{1d\_spectral}(H_s, T_p)$ 100ms 超速頻譜預報[cite: 3, 7]$T_p > 10.0\text{ s}$ 且 $H_s > 0.90\text{ m}$ 發動港池能量穿透熔斷[cite: 3, 7]。6. 邊坡崩塌風險$Risk \le 0.60$[cite: 6, 7]ARDSWC 龜首崩塌事件同化算子[cite: 6, 7]龜首崩塌風險比率 $> 0.60$ 強制阻斷[cite: 6, 7]。7. 官方公告 (Ch 37)$Status = 0.0$  東北角風管處官網新聞爬取引擎[cite: 3, 7]官網發布封島通告 ($Status = 1.0$) 10 秒最高優先級寫入 SSOT[cite: 3, 5, 7]。自適應下修係數：$\alpha_{\text{adaptive}} \in [0.65, 1.00]$，由歷史智庫 (KB_20260904_ESE_OVERTOPPING) 與奇門解盲匹配率（$\ge 70\%$）自動導出[cite: 3, 6, 7]。三、 Level 5 高維邊緣算子與 MLOps 閉環Vision-PINN 邊緣視覺越浪算子 (VisionPINNEdgeNet)：解析 128x128 影像張量，進行多天候自监督學習，即時估算越浪率（$\text{p/min}$）[cite: 3, 7]。一旦偵測浪面蓋頂（越浪率 $> 0\text{ p/min}$），硬性覆寫乾舷 $FB_{pier} = 0.15\text{ m} < 0.50\text{ m}$ 阻斷放行[cite: 3, 7]。FNO 100ms 超速頻譜算子 (FNO1dWaveSpectralForecaster)：採用 1D 傅立葉神經算子，於 100ms 內推演未來 3 小時港池平均波高演化[cite: 3, 7]。MMSI 專屬水動力算子 (VesselMMSIHydrodynamics)：動態擷取 TDX AIS 10秒級航速，精算雙體客輪（凱鯨號）動態蹲沉量 $Squat = 0.08 \cdot v^2 / 9.81 = 0.82\text{ m}$，消除 $UKC$ 盲區[cite: 3, 7]。  64D 太乙奇門量子拓撲同化器 (QuantumTopology64DEngine)：同化 18.6 年白道交角與 60 年甲子公度歷史週期[cite: 1, 4, 5, 7]。當奇門氣場匹配率 $\ge 70\%$ 時解鎖 Attention Gate ($Macro\ Bias = 0.40$)，主動緊縮門檻 $\alpha_{\text{adaptive}}$ 實現超前解盲[cite: 3, 5, 6, 7]。Colab 雲端自動 Git 同步器 (sync_to_github_repository)：在 Colab 執行 execute_master_pipeline() 後，自動調用注入之 GITHUB_TOKEN 提交 latest_decision.json 並 Git Push 至 marlinx-neyc/gem-engine 儲存庫 main 分支[cite: 5, 6, 7]，觸發 GitHub Actions 30–60 秒內完成 GitHub Pages 部署，徹底解決時間停滯問題。  四、 T-30/T-45/T-60 預警向量與游擊時窗調度 (Early Warning & Guerrilla Dispatch)預警等級觸發指標與算子戰術指令與處置燈號狀態T - 60 min (氣場解盲)奇門同化匹配率 $\ge 70\%$[cite: 6, 7]解鎖 Attention Gate ($Macro\ Bias = 0.40$)[cite: 3, 6, 7]，主動緊縮門檻 $\alpha \le 0.85$[cite: 3, 7]🟡 氣場預警[cite: 6, 7]T - 45 min (湧浪海象)$H_s > 1.00\text{ m}$ 或長浪 $T_p > 10.0\text{ s}$[cite: 6, 7]港池共振穿透預警[cite: 3, 6, 7]，動態壓縮止登時間 $T_{\text{stop}}$[cite: 6, 7]🟡 湧浪陡升[cite: 6, 7]T - 30 min (移防調撥)風向偏轉 $\Delta\theta \ge 35^\circ$ 且橫流 $\ge 1.8\text{ kts}$[cite: 6, 7]指引移防切換至【南岸權宜碼頭】靠泊[cite: 6, 7]🟡 移防指引[cite: 6, 7]T - 0 min (剛性熔斷)觸發任一 VETO 物理極值或官方公告[cite: 3, 6, 7]判定【防颱避風/禁止靠泊】，全員撤離返航【烏石港】[cite: 3, 6, 7]🔴 剛性熔斷[cite: 6, 7]游擊時窗排程：10:50 / 13:50 半小時預發雙警報[cite: 6, 7]；11:20 執行止登【南岸碼頭】[cite: 6, 7]；14:20 全員清島撤離返航【烏石港】避風[cite: 6, 7, 9]。五、 37D 特徵空間、LoRA 影子微調與 Monte Carlo Auto-Gate37D 歸一化特徵提取器 (GEM37DNormalizedFeatureExtractor)：將遙測水文、風速、潮位、坡體風險、奇門匹配率與第 37 通道（官方封島公告狀態 $0.0/1.0$）進行 37D 邊界歸一化，解決舊版 36D 權重相容 mismatch 問題[cite: 3, 5, 6, 7]。咸恆 LoRA 影子微調 (XianHengAutonomousShadowTrainer)：當出現「官方封島 ($1.0$) ✕ 模型放行 ($0.0$)」或公務船退回之衝突殘差時，給予 $-9999$ 致命懲罰並啟動 LoRA ($\text{Rank} = 4$) 適配器增量訓練[cite: 3, 5, 6, 7, 8, 9]。Monte Carlo Auto-Gate 驗證：影子適配器需通過 1,000 次物理沙盒擾動演練，通過率 $\ge 95\%$ 且險卦（坎、屯、蹇、困）零違例後，熱替換（Hot-Swap）覆寫持久化導出 model_v36D_latest.pt[cite: 3, 5, 6, 7]。六、 雙端 DOM 幾何佈局與三方案 Ground Truth 規範CSS/* 頂、左、右雙欄剛性幾何鎖定 (CLS = 0) */
.dashboard-header-master { width: 100%; height: 120px; contain: strict; }
.dashboard-main-layout   { display: flex; gap: 20px; width: 100%; }
.layout-left-tactical    { flex: 0 0 35%; max-width: 35%; contain: content; }
.layout-right-charts     { flex: 0 0 65%; max-width: 65%; contain: content; }
1. 桌面端 (desktop.html) 35% / 65% 剛性雙欄置頂一體化卡片 (header-master-card)：120px 剛性高度，置頂 ● LIVE SSOT 動態藍呼吸燈、連線計數、AI 雙核指標區（信心度 100.0%、$\sigma = 0.3125$）與平行 4 大 Level 5 微型算子卡片[cite: 6, 7]。左欄戰術控制區 (35% 欄寬)：包含 PINN 4 項水文門檻比對、當日/明日開封島預警時窗（嵌入高光黃戰略總結）、⚓ 游擊式動態調度卡片（#f59e0b 邊框）與 🌀 颱風/長浪/奇門氣場卡片（#a855f7 邊框）[cite: 6, 7]。右欄圖表陣列 (65% 欄寬)：2x2 時間線圖表矩陣（11:20 止登 / 14:20 撤離無箭頭虛線）、未來 7 天雙軸趨勢圖及底部 Ground Truth 三方案評估比對表格（方案 C 高光黃 #facc15 標註）[cite: 6, 7]。2. 手持端 (mobile.html) 100% 垂直單欄流嚴禁加載 ECharts DOM，全數據使用 node.textContent 寫入。卡片依序為：● LIVE SSOT 狀態卡、Watchdog 數據過期 Banner、Q-Mode 戰術裁決 Banner、PINN 水文極值、預警時窗與預測卡、⚓ 游擊調度卡、🌀 奇門氣場卡、🚀 Level 5 算子卡與 Ground Truth 三方案對比卡[cite: 6, 7]。  七、 標準 SSOT JSON Schema 規範 (v36D.200.0)JSON{
  "version": "v36D.200.0 Qimen Unblind & Official Closure RL Master",
  "timestamp": "2026-09-15 18:35:00 CST",
  "decision": "🔴 封島/防颱",
  "confidence_score": 100.0,
  "confidence_label": "🟢 100.0% [完整同化 PASS]",
  "hard_veto_alert": true,
  "physics_metrics": {
    "hs_pier_m": 3.71,
    "w_local_ms": 8.50,
    "w_effective_ms": 5.98,
    "tide_eta_m": 1.00,
    "s_quat_m": 0.82,
    "ukc_m": 0.27,
    "fb_pier_m": 0.15,
    "slope_landslide_risk": 0.15,
    "adaptive_alpha": 0.85,
    "historical_similarity": 0.92,
    "has_veto": true
  },
  "guerrilla_dispatch": {
    "berthing_pier": "【防颱避風/禁止靠泊】",
    "evacuation_pier": "【強制撤離】 -> 返航【烏石港】",
    "early_warning_vector": {
      "t60_qimen_warning": "🟡 T-60 氣場預警：奇門同化匹配率 100.0% >= 70%，已解鎖 64D 拓撲 Macro Bias 0.40",
      "t45_wave_steep_warning": "🟡 T-45 湧浪海象預警：長浪週期 Tp=15.5s (>10.0s Kd=1.00 港池共振) 趨勢預警",
      "t30_pier_shift_warning": "🟡 T-30 移防預警：風向偏轉 (Δθ=45.0° >= 35° 側風) 且橫流 0.9kts，指引切換至【南岸權宜碼頭】"
    },
    "tactical_summary": "⚠️ 三方案定性定量總結：方案A與方案B預判放行/限縮；方案C(GEM-V36D Ground Truth)精確比對全海象歷史智庫與奇門解盲(α=0.85)，判定【剛性熔斷】！游擊調度決策：官方公告預警封島。建議 11:20 止登，14:20 全員撤離至烏石港。",
    "t_stop_window": "11:20",
    "t_evac_window": "14:20",
    "is_backup_mode": false,
    "open_island_0730": "🔴 封島",
    "open_island_1630_tomorrow": "🔴 預警封島"
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
    "qimen_status_prompt": "🔮 奇門氣場匹配率達 100.0% (>=70%)，已啟動 Attention Gate 宏觀解盲與預警性門檻對齊"
  }
}
