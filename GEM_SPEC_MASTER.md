# GEM-SPEC-2026-V43: 龜山島海事戰術動態調和系統工程規範

**文件編號**：GEM-ENG-SPEC-2026-V43  
**密級標籤**：生產級核心技術規範 (Production Standard)  
**生效日期**：2026-10-13  
**適用範圍**：龜山島海域客輪航行、碼頭靠泊調度、防災應急避險與自主學習主控系統[cite: 2, 8]

---

## 1. 文件基本資訊與系統定義

### 1.1 系統使命
本系統（GEM Engine v43.0 Master / v66.0 Unified Orchestrator）為龜山島海事戰術指揮智庫之最高 AI 主控大腦[cite: 2, 3, 8]。系統宗旨在於將《易經》「執兩用中」哲學深度轉化為約束馬可夫決策過程（Constrained Markov Decision Process, CMDP），解決傳統二分法（非開即封）在佔全年營運時間 85% 以上之灰色過渡態（中間 62 卦）頻繁引發的「誤判開島（坐灘翻船）」與「過度停航（扼殺營運）」問題[cite: 2, 8]。

### 1.2 控制論架構：執兩用中
* **執兩（剛性邊界約束）**：
  * **純乾極陽邊界（100.0% 放行）**：環境能量完全受控，四層物理防線全數通過，系統零干預常態通行[cite: 2, 8]。
  * **純坤極陰邊界（0.0% 熔斷）**：一旦遭遇港池長浪消能瓦解或水下觸底坐灘風險，一票否決觸發 Hard VETO 剛性熔斷，全線封島[cite: 2, 8]。
* **用中（62 卦灰色相變調和）**：
  在兩極邊界之間，主動釋放**「航速連續調控（消減蹲沉）」**、**「雙岸空間位移（背風掩蔽）」**與**「時域非線性截斷（動態時窗）」**三個控制自由度，以人為損益陰陽，維持流形空間動態平衡[cite: 2, 8]。

---

## 2. 立體多維物理感知硬體與通信規範

### 2.1 X-band 高頻雷達與波浪頻譜儀
* **採樣頻率**：$\ge 10\text{ Hz}$，方向解析度 $\le 2.5^\circ$，頻率解析度 $\le 0.01\text{ Hz}$[cite: 2, 8]。
* **物理功能**：即時解算二維方向波能譜 $S(f, \theta)$，提取譜峰頻率 $f_p$ 與湧浪週期 $T_p = \frac{1}{f_p}$[cite: 2, 8]。
* **港池共振消能崩潰判定**：
  當低頻能量通量佔比 $> 35\%$ 或 $T_p \ge 12.0\text{ s}$ 時，港池防波堤繞射消能機制完全崩潰，繞射消能因子強制覆寫為 $K_d = 1.00$[cite: 2, 8]。

### 2.2 AIS-GEBCO 載具雙生融合模組
* **AIS 協議**：Class A 載具動態更新週期 $\le 2.0\text{ s}$，網路延遲 $\le 500\text{ ms}$[cite: 2, 8]。
* **高解析度水深數據庫**：融合 GEBCO 2024 與電子海圖（ENC）10m 網格數據（北岸基線水深 $-8.50\text{ m CD}$，南岸浚挖水深 $-9.80\text{ m CD}$）[cite: 2, 3, 8]。
* **動態淺水蹲沉方程（Squat）**[cite: 2, 8]：
  $$F_h = \min\left(0.95, \; \frac{V_{\text{speed}} \cdot 0.514444}{\sqrt{g \cdot d_{\text{chart}}}}\right)$$
  $$S_{\text{squat}} = \frac{C_B \cdot V_{\text{speed}}^2}{30 \cdot (d_{\text{chart}} / d_{\text{draft}})} \cdot \frac{1}{\sqrt{\max(0.05, 1 - F_h^2)}} \cdot 0.50$$
  *(基準客輪參數：方形係數 $C_B = 0.65$，靜吃水 $d_{\text{draft}} = 1.20\text{ m}$ 至 $2.02\text{ m}$；12.5 節常速時 $S_{\text{squat}} = 0.82\text{ m}$，指令限速 3.0 節時 $S_{\text{squat}} = 0.15\text{ m}$)*[cite: 2, 3, 8]。

### 2.3 Vision-PINN 引橋邊緣光學感知儀
* **邊緣硬體規格**：防鹽霧邊緣 AI 攝影機，幀率 $\ge 30\text{ FPS}$，推理時延 $\le 33\text{ ms}$[cite: 2, 8]。
* **越浪量化指標**：邊緣神經網路捕捉碎波翻越引橋的高程與頻次，輸出即時越浪率 $CV$（次/分鐘）[cite: 2, 8]。
* **覆寫協議**：一旦檢測到 $CV > 0.0\text{ p/min}$，系統於 $100\text{ ms}$ 內將預留乾舷強制覆寫為 $FB = 0.15\text{ m}$[cite: 2, 8]。

### 2.4 雙岸差分氣象超音波風速儀
* **測站佈局**：分別部署於北岸碼頭引橋與南岸權宜碼頭泊位[cite: 2, 8]。
* **掩蔽係數解算 ($K_w$)**[cite: 2, 8]：
  $$K_w = \frac{W_{\text{local, pier}}}{W_{\text{CWA, offshore}} \cdot \vert{}\cos(\Delta\theta)\vert{}}$$
  當風向攻角 $\Delta\theta < 35^\circ$ 且南岸受風時，$K_w = 0.78$（401 高地吸收 22% 風能）；$35^\circ \le \Delta\theta < 45^\circ$ 時，$K_w = 0.88$；$\Delta\theta \ge 45^\circ$ 時，$K_w = 1.00$（掩蔽完全失效）[cite: 2, 8]。

### 2.5 氣象署 (CWA) 與國家防救災中心 (NCDR) 外部即時資料管線規範
* **CWA 颱風警報 API 連線**：直接介接氣象署 OpenData API（資料集代碼：`W-C0034-001`），動態解算颱風中心即時經緯度、強度、暴風半徑與龜山島之球面距離（Haversine 距離公式）。
* **行政應變三欄同步規範**：主控管線強制連動「中央災害應變中心」、「宜蘭縣災害應變中心」與「新北市災害應變中心」之即時開設層級（未開設 / 二級開設 / 一級開設），任何一處啟動一級開設即聯鎖觸發防颱管制[cite: 1, 3]。
* **NCDR 官方路徑圖資容災**：優先載入氣象署即時警報圖資（`https://www.cwa.gov.tw/Data/typhoon/TY_WARN/B20.png`），若通訊受阻自動無縫切換為 NCDR 備用圖資（`https://watch.ncdr.nat.gov.tw/watch_filename/typhoon_route.png`）[cite: 3]。

---

## 3. 四層剛性物理防線（Hard VETO Physics Matrix）

決策遵循「一票否決（Hard VETO）」原則，任一物理防線未通過即強制觸發純坤熔斷[cite: 2, 8]：
$$\text{Hard\_Veto} = \text{Veto}_{Hs} \lor \text{Veto}_{W} \lor \text{Veto}_{UKC} \lor \text{Veto}_{FB}$$

| 防線層級 | 物理指標 | 量化精算公式 / 條件約束 | 剛性通過門檻 | 違規危害等級 |
| :--- | :--- | :--- | :---: | :--- |
| **第一層【太陽：波能】** | 港池折算波高 $H_{s,pier}$ | $H_{s,pier} = H_{s,cwa} \cdot K_d(T_p) + \text{PINN\_offset}$<br>*(若 $T_p \ge 12.0\text{ s} \implies K_d = 1.00$)*[cite: 2, 8] | $H_{s,pier} \le 1.13\text{ m}$[cite: 2, 8] | 🔴 港池共振、船舶劇烈搖晃斷纜翻覆[cite: 2, 8] |
| **第二層【少陽：風能】** | 攻角有效風速 $W_{eff}$ | $W_{eff} = W_{cwa} \cdot \vert{}\cos(\Delta\theta)\vert{} \cdot K_w$<br>*(若 $\Delta\theta \ge 45^\circ \implies K_w = 1.00$)*[cite: 2, 8] | $W_{eff} \le 10.17\text{ m/s}$[cite: 2, 8] | 🔴 橫風橫流推擠、難以控舷撞擊碼頭[cite: 2, 8] |
| **第三層【少陰：底阻】** | 動態安全裕深 $UKC$ | $UKC = (d_{chart} + \eta_{tide}) - (d_{draft} + S_{squat}) - H_{s,pier}$<br>*(航速 12.5 kts 時 $S_{squat}=0.82\text{m}$；限速 3.0 kts 時 $S_{squat}=0.15\text{m}$)*[cite: 2, 8] | $UKC \ge 1.50\text{ m}$[cite: 2, 8] | 🔴 船底龍骨直接碰撞海底拋石坐灘[cite: 2, 8] |
| **第四層【太陰：頂阻】** | 預留乾舷高程 $FB_{pier}$ | $FB_{pier} = 3.20\text{ m} - \eta_{tide}$<br>*(若 $CV > 0.0\text{ p/min} \implies FB_{pier} = 0.15\text{ m}$)*[cite: 2, 8] | $FB_{pier} \ge 0.50\text{ m}$[cite: 2, 8] | 🔴 引橋遭碎波淹沒漫頂、旅客踏空落海[cite: 2, 8] |

---

## 4. 全域能量張量與 Fermi-Dirac 相變機率算子

### 4.1 兩儀動能阻抗平衡
將多維水文環境升維折算為全域等效能量標量 $\mathcal{E}_{net}$[cite: 2, 8]：
$$\mathcal{E}_{net} = \frac{\mathcal{K}_{\text{陽儀動能通量}}}{\mathcal{V}_{\text{陰儀勢能阻抗}}} = \frac{H_{s,pier} + (W_{eff} \cdot 0.1) + S_{\text{squat}}}{0.5 \cdot UKC + 0.5 \cdot FB_{\text{pier}}}$$

### 4.2 Fermi-Dirac 光滑相變風險函數
消除傳統階躍門檻在臨界點的斷崖突變，計算破防相變機率 $P_{\text{veto}}$[cite: 2, 8]：
$$P_{\text{veto}} = \frac{1}{1 + \exp\left( -\frac{\mathcal{E}_{net} - \mathcal{E}_{crit}}{\beta \cdot \alpha_{tune}} \right)}$$
* $\mathcal{E}_{crit} = 1.00$（臨界平衡標量），$\beta = 0.25$（相變溫度係數），$\alpha_{tune} \in [0.75, 0.95]$（RL 自適應緊縮係數）[cite: 2, 8]。
* **狀態判準律**[cite: 2, 8]：
  * $P_{\text{veto}} < 0.20$：純乾卦（Action 2: 🟢 100.0% Q1 全線常態開放）[cite: 2, 8]。
  * $P_{\text{veto}} > 0.80$：純坤卦（Action 0: 🔴 0.0% 剛性熔斷全線封島）[cite: 2, 8]。
  * $0.20 \le P_{\text{veto}} \le 0.80$：中間 62 卦灰色過渡帶，強制啟動 YZ-RL 主動調和戰術（Action 1: 🟡 Q2 游擊調撥 或 Action 3: ⏱️ Q3 動態開窗）[cite: 2, 8]。

---

## 5. 14 維正交物理基底特徵展開規範（Orthogonal Physics Bases）

為消除非線性特徵間的線性串擾（Cross-talk），狀態向量必須嚴格投影至 14 維正交基底空間 $\phi(\mathbf{s})$[cite: 2, 8]：

$$\phi(\mathbf{s}) = \begin{bmatrix} 1.0 & \text{// 1. 基礎 Bias 偏置常數項} \\ H_{s,cwa} / 2.0 & \text{// 2. 外海波高正規化標量} \\ W_{cwa} / 12.0 & \text{// 3. 外海風速正規化標量} \\ T_{p,s} / 15.0 & \text{// 4. 湧浪週期正規化標量} \\ \eta_{tide} / 1.5 & \text{// 5. 動態潮位正規化標量} \\ \Delta\theta / 45.0 & \text{// 6. 風向攻角正規化標量} \\ CV / 2.0 & \text{// 7. 越浪率正規化標量} \\ \text{Match}_{rate} & \text{// 8. 歷史吻合度 (0.75 ~ 0.96)} \\ \mathbf{B}_{\text{clear}} & \text{// 9. 晴朗常態基底 } (H_s \le 0.95 \land T_p < 10.0 \land CV = 0.0 \land \eta \ge 0.6) \\ \mathbf{B}_{\text{squat}} & \text{// 10. 低潮蹲沉基底 } (\eta < 0.40 \land V_{\text{speed}} \ge 10.0\text{ kts}) \\ \mathbf{B}_{\text{swell}} & \text{// 11. 長浪穿透基底 } (T_p \ge 12.0\text{ s} \land H_s > 0.90\text{ m}) \\ \mathbf{B}_{\text{overtop}} & \text{// 12. 引橋越浪基底 } (CV \ge 1.0\text{ p/min}) \\ \mathbf{B}_{\text{wind\_south}} & \text{// 13. 南岸掩蔽基底 } (35.0^\circ \le \Delta\theta < 45.0^\circ) \\ \mathbf{B}_{\text{veto}} & \text{// 14. 極端熔斷基底 } (H_s \ge 2.2\text{ m} \lor W \ge 13.0\text{ m/s}) \end{bmatrix}$$

---

## 6. YZ-RL 雙 Q 強化學習與優先級經驗回放協議

### 6.1 優先級經驗回放（PER Buffer）
* **緩衝區容量**：$Capacity = 3000$，超額時以 FIFO 淘汰最低優先級樣本[cite: 2, 8]。
* **採樣機率分佈**[cite: 2, 8]：
  $$P(i) = \frac{p_i^\alpha}{\sum_k p_k^\alpha}, \quad p_i = \left( \vert{}\text{TD-error}_i\vert{} + 10^{-4} \right)^\alpha \quad (\alpha = 0.6)$$
* **重要性採樣權重（Importance Sampling）**[cite: 2, 8]：
  $$w_i = \frac{(N \cdot P(i))^{-\beta}}{\max_k(w_k)} \quad (\beta \text{ 自 0.4 線性退火至 1.0})$$

### 6.2 雙 Q 網絡軟更新機制（Target-Q Soft Update）
* **超參數**：學習率 $\alpha = 0.035$，折扣因子 $\gamma = 0.92$，Polyak 軟更新係數 $\tau = 0.05$[cite: 2, 8]。
* **時序差分誤差（TD-Error）**[cite: 2, 8]：
  $$\text{TD-error} = \left( Reward + \gamma \cdot \max_{a'} Q_{\text{target}}(\mathbf{s}', a') \right) - Q_{\text{eval}}(\mathbf{s}, a)$$
* **梯度更新與軟更新公式**[cite: 2, 8]：
  $$W_{\text{eval}}[:, a] \leftarrow W_{\text{eval}}[:, a] + \alpha \cdot \text{TD-error} \cdot \phi(\mathbf{s}) \cdot w_i$$
  $$W_{\text{target}} \leftarrow (1 - \tau) W_{\text{target}} + \tau W_{\text{eval}}$$

### 6.3 獎勵函數工程矩陣（Reward Matrix）
* **化險為夷最優解（Action 1 / 移防南岸 + 限速 3 節）**：$+18.0$[cite: 2, 8]。
* **剛性熔斷正確避險（Action 0 / 熔斷長浪共振或極端風暴）**：$+18.0$[cite: 2, 8]。
* **動態開窗最優解（Action 3 / 滿潮越浪及時止登清島）**：$+16.0$[cite: 2, 8]。
* **常態通航最優解（Action 2 / 晴朗平穩靠泊北岸）**：$+16.0$[cite: 2, 8]。
* **盲目冒進巨額懲罰（長浪共振穿透或水下蹲沉觸底冒進）**：$-35.0$[cite: 2, 8]。
* **過度停航誤封懲罰（晴朗無風條件下誤宣告封島）**：$-20.0$[cite: 2, 8]。

---

## 7. 態互歷史蒸餾器標準（FAISS 90% 目標 / 75% 底線）

### 7.1 吻合度計算與在線反饋閉環方程
$$\text{Penalty} = \max(0.0, (H_{s,cwa} - 1.1) \cdot 0.05) + \max(0.0, (1.5 - UKC) \cdot 0.06)$$
$$\text{learned\_bias} \leftarrow \operatorname{clip}\left(\text{learned\_bias} + Reward \cdot 0.0004, \; -0.03, \; 0.06\right)$$
$$\text{Match}_{rate} = \operatorname{clip}\left(0.90 - \text{Penalty} + \text{learned\_bias}, \; 0.75, \; 0.96\right)$$

### 7.2 質量控制指標
* **常態海況**：歷史吻合度穩定落在 **93.8% ~ 95.0%** 置信區間[cite: 2, 8]。
* **極端暴風海況**：歷史吻合度剛性維持於 **75.0% 底線以上**（實測維持在 **83.0%**），杜絕 AI 外推幻覺[cite: 2, 8]。

---

## 8. 現場戰術調度、行動映射與應急時程規範

### 8.1 四態戰術行動映射集（Tactical Action Set）

| 動作代碼 | 戰術名稱 | 卦象映射 | 觸發邊界條件 | 航速限制 | 泊位配置 | 時窗管制 |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- |
| **`0`** | **🔴 0.0% 物理熔斷**[cite: 2, 8] | 純坤 | $T_p \ge 12.0\text{ s}$ 或四層防線破防[cite: 2, 8] | $0.0\text{ kts}$ | 雙岸失效禁止靠泊[cite: 2, 8] | 全天剛性封閉[cite: 2, 8] |
| **`1`** | **🟡 Q2 游擊調撥**[cite: 2, 8] | 水山蹇 / 風水渙 | 退潮低水位或 $\Delta\theta \in [35^\circ, 42^\circ]$[cite: 2, 8] | **強制 $\le 3.0\text{ kts}$**[cite: 2, 8] | 移防南岸權宜碼頭[cite: 2, 8] | 常態通航視窗[cite: 2, 8] |
| **`2`** | **🟢 100.0% Q1 全線開放**[cite: 2, 8] | 純乾 / 中孚 | 全線通過，波平浪靜 | 常規 $\le 12.0\text{ kts}$[cite: 2, 8] | 北岸碼頭主泊位[cite: 2, 8] | 全天優良視窗[cite: 2, 8] |
| **`3`** | **⏱️ Q3 動態開窗**[cite: 2, 8] | 水澤節 / 水天需 | 滿潮 $CV > 1.0\text{ p/m}$ 或午後退潮變天[cite: 2, 8] | 謹慎 $\le 8.0\text{ kts}$[cite: 2, 8] | 北岸碼頭限時泊位[cite: 2, 8] | **11:20 止登 / 14:20 撤離**[cite: 2, 8] |

### 8.2 當日關鍵管制時程節點
* **07:30**：晨間第一階段開島初審（比對外海浮標與現場頻譜儀）[cite: 2, 8]。
* **10:00**：滿潮高水位窗口（水深充裕但啟動 Vision-PINN 監控引橋漫頂）[cite: 2, 8]。
* **10:50**：預警廣播節點（廣播提醒即將關閉登島引橋）[cite: 2, 8]。
* **11:20 關鍵止登節點**：剛性關閉登島引橋，全線嚴禁新增遊客登島[cite: 2, 8]。
* **13:50**：清島預警廣播（全島廣播提醒遊客前往碼頭候船撤離）[cite: 2, 8]。
* **14:20 強制清島撤離節點**：全島清空全員登船，直航返航頭城烏石港[cite: 2, 8]。
* **16:30**：發布次日開島海象預報[cite: 2, 8]。

### 8.3 避難撤離耗時精算公式
$$Evac\_Minutes = \left\lceil \frac{Passenger\_Count}{10} + \max(0.0, (S_{\text{squat}} - 0.50) \cdot 15.0) + 5.0 \right\rceil$$
*(基準配置：150 名遊客、常速蹲沉 0.82m 條件下，精算撤離耗時恆為 25 分鐘；限速 3.0 節蹲沉 0.15m 時，耗時縮減至 20 分鐘)*[cite: 2, 8]。

### 8.4 牛奶海酸泉擴散禁戒規範
滿潮後 3.
