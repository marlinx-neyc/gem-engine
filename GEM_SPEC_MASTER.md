# GEM_SPEC_MASTER.md
# GEM-V40「大道至簡・道器合一」海事數位雙生戰術控制台暨自主進化智庫最高技術規格檔

**文件版本**：v40.0 Complete Master Autonomous & Da Dao Production Edition[cite: 22]  
**生效日期**：2026-10-13[cite: 22]  
**適用範疇**：後端 Python SSOT 狀態中樞、RL 自適應強化學習算子、前端幾何絕對凍結控制台、各工具物件化模組 (OOP Widgets)、跨模組事件總線 (EventBus) 與權威總裁示稽核存根[cite: 22]。

---

## 1. 哲學總綱、SSOT 合約與戰略二元坍縮 (Philosophy & Binary Collapse)

### 1.1 道器合一方法論溯源
當代海事工程與決策極易陷入西方還原論的「拆零泥淖」：將波高、風速、週期、攻角、潮位拆解得極其細碎，卻忘記如何將其組裝為一體場域，導致前額葉認知超載與系統失律[cite: 1, 22]。  
本規範落實邵雍「合一斯為一，衍之斯為萬」與「四象收斂為兩儀，兩儀收斂為太極」之哲學體系[cite: 1]：
- **太極一元（道）**：戰略決斷最終必須收斂為二進制指令：**要（1，全線開放靠泊）** 或 **不要（0，0.0% 物理熔斷/全線封島）**[cite: 1, 22]。生死關頭嚴禁給出模糊不決的折衷推論[cite: 1]。
- **兩儀平衡（理）**：多維環境特徵向量統一轉換為**全域等效能量標量 $\mathcal{E}_{net}$**，由**陽儀（外海動能通量 $\mathcal{K}$）**與**陰儀（泊位勢能與幾何阻抗 $\mathcal{V}$）**的動態消長決定[cite: 1, 22]。
- **四象器用（器）**：立不易方，將剛性防線卡、雙岸子彈儀、六軸雷達、水下防碰撞雙斷面剖面儀等工具全面物件化解耦，純數據注入驅動[cite: 1, 22]。

### 1.2 單一真實數據源 (SSOT) 與握手協定
1. **SSOT 唯一狀態中樞**：後端由 Python 統合引擎每秒解算並輸出唯一決策封包至 `latest_decision.json`[cite: 3, 7]。前端所有視覺工具箱與 AI 專家顧問均為消費者，強制採納該數據作為唯一真實基準 (Ground Truth)[cite: 7, 22]。
2. **剛性稽核前置檢核**：
   $$\text{Audit\_Pass} = \left( H_{s,pier} \le 1.13\text{ m} \right) \land \left( W_{eff} \le 10.17\text{ m/s} \right) \land \left( UKC \ge 1.50\text{ m} \right) \land \left( FB_{pier} \ge 0.50\text{ m} \right)$$
[cite: 7]
   若 $\text{Audit\_Pass} = \text{False}$，系統強制將狀態標記為 `🔴 0.0% 物理 VETO 熔斷`，並觸發全線封島管制指令[cite: 7, 22]。

---

## 2. 四大工程幾何與軟體剛性架構法則 (The 4 Methodological Pillars)

### 2.1 法則一：【立不易方】容器幾何絕對凍結 (CLS = 0)
1. 外觀佈局、容器邊界、Canvas 尺寸在頁面載入第 0 毫秒即宣告定型，累計版面位移 (CLS) 恆等於 0[cite: 1, 22]。
2. 每個工具在 HTML 中只佔據封閉、具備固定尺寸邊界的獨立外殼（`contain: content`）[cite: 1, 22]。
3. 嚴禁在執行階段動態重組結構或以 `innerHTML` 拼裝父級 DOM 節點，杜絕排版重繪與幾何錯位[cite: 1, 22]。

### 2.2 法則二：【變動不居，出入以度】純數據單向注入管線
1. 所有感測數據統一匯入中央狀態引擎 (`CentralStateEngine`)[cite: 1, 22]。
2. 各視覺工具箱抽象為標準類別 (`Widget Class`)，僅暴露標準單一介面 `widget.update(data)`，內部僅以 `textContent` 或 Canvas 重繪填入數值，嚴禁跨界向外竄改鄰近物件[cite: 1, 22]。
3. **獨立保險絲 (Error Boundary)**：每個工具的更新邏輯必須由獨立 `try...catch` 完整包覆[cite: 1, 22]。任一 Canvas 繪圖坐標異常報錯，防線卡與子彈條依然以 100% 精確度運行，核心海事裁決不受干擾[cite: 1, 22]。

### 2.3 法則三：【一而二，二而一】能量張量轉換
定義輸入環境狀態特徵向量：
$$\mathbf{X} = \begin{bmatrix} H_{s,CWA} \\ W_{local} \\ T_p \\ \vert\cos(\Delta\theta)\vert \\ \eta_{tide} \end{bmatrix} \in \mathbb{R}^5$$
[cite: 1]
透過空間攻角、地形阻抗與水深濾波基係數矩陣 $\mathbf{M}(\Delta\theta, T_p, d_{chart})$，折算為碼頭泊位承受之**全域等效紊動通量標量**[cite: 1]：
$$\mathcal{E}_{net} = \mathbf{X}^T \mathbf{M} \mathbf{X} = \mathcal{K}_{\text{陽儀動能通量}} - \mathcal{V}_{\text{陰儀勢能阻抗}}$$
[cite: 1]
- **陽儀動能通量 ($\mathcal{K}$)**：外海波能密度 $\frac{1}{8}\rho g H_s^2$ 與局域風剪應力 $\frac{1}{2}\rho_{air} W^2$[cite: 1]。長浪週期 $T_p > 12.0\text{ s}$ 觸發長浪港池共振時，繞射消能瓦解，$K_d = 1.00$[cite: 1, 22]；風向攻角 $\Delta\theta \ge 45^\circ$ 時，401 高地背風屏障失效，$K_w = 1.00$[cite: 1, 22]。
- **陰儀勢能阻抗 ($\mathcal{V}$)**：水深底質空間裕度位能與碼頭乾舷重力勢壘[cite: 1]。穿浪雙體客輪靜吃水 $1.20\text{ m}$ 疊加淺水高速蹲沉 $S_{squat}=0.82\text{ m}$，動態吃水包絡線固定佔用 $2.02\text{ m}$[cite: 1, 2, 22]。

### 2.4 法則四：【太極一元】戰略二元坍縮
設定安全臨界勢壘 $\mathcal{E}_{crit} = 1.00$ 與熔斷上限 $1.25\,\mathcal{E}_{crit}$[cite: 1, 22]：
$$\text{Strategic Ruling} = \begin{cases} \mathbf{1} \text{ (要：全線開放靠泊)} & \text{若 } \mathcal{E}_{net} \le \mathcal{E}_{crit} \land \text{Hard\_Veto} = \text{False} \\ \mathbf{0} \text{ (不要：0.0\% 物理熔斷 / 全線封島)} & \text{若 } \mathcal{E}_{net} > 1.25\,\mathcal{E}_{crit} \lor \text{Hard\_Veto} = \text{True} \end{cases}$$
[cite: 1, 22]

---

## 3. 微觀水動力四層剛性防線合約 (Hard VETO Physics Matrix)

剛性防線遵循一票否決制：$\text{Hard\_Veto} = \text{Veto}_{Hs} \lor \text{Veto}_{W} \lor \text{Veto}_{UKC} \lor \text{Veto}_{FB}$[cite: 7]。

| 防線層級 | 物理指標 | 遲滯精算公式與破防機制 | 剛性通過門檻 ($\alpha_{tune}=0.90\sim0.94$) | 狀態燈號表現 |
| :--- | :--- | :--- | :--- | :--- |
| **第一層【太陽：波能】** | 港池有效波高 $H_{s,pier}$ | $H_{s,pier} = H_{s,CWA} \cdot K_d(T_p) + PINN_{offset}$<br>若 $T_p > 12.0\text{ s} \implies K_d = 1.00$ (長浪擊穿消能)[cite: 1, 7] | $H_{s,pier} \le 1.13\text{ m}$[cite: 1, 7] | Pass: 🟢 `text-emerald-400`<br>Fail: 🔴 `text-red-400` (超標)[cite: 7] |
| **第二層【少陽：風能】** | 攻角有效風速 $W_{eff}$ | $W_{eff} = W_{local} \cdot \vert\cos(\Delta\theta)\vert \cdot K_w$<br>若 $\Delta\theta \ge 45^\circ \implies K_w = 1.00$ (背風屏障失守)[cite: 1, 7] | $W_{eff} \le 10.17\text{ m/s}$[cite: 1, 7] | Pass: 🟢 `text-emerald-400`<br>Fail: 🔴 `text-red-400` (橫風)[cite: 7] |
| **第三層【少陰：底阻】** | 動態安全裕深 $UKC$ | $UKC = (d_{chart} + \eta_{tide}) - 2.02\text{ m} - H_{s,pier}$<br>(北岸拋石 -3.20m CD / 南岸浚挖 -5.50m CD)[cite: 2, 7] | $UKC \ge 1.50\text{ m}$[cite: 1, 7] | Pass: 🟢 `text-emerald-400`<br>Warn: 🟡 `text-amber-300`<br>Fail: 🔴 `text-red-400` (觸底/坐灘)[cite: 7] |
| **第四層【太陰：頂阻】** | 預留乾舷高程 $FB_{pier}$ | $FB_{pier} = Deck_{elev} - \eta_{tide}$<br>若 Vision-PINN 越浪率 $CV > 0\text{ p/m} \implies FB_{pier} = 0.15\text{ m}$ (覆寫)[cite: 1, 7] | $FB_{pier} \ge 0.50\text{ m}$[cite: 1, 7] | Pass: 🟢 `text-emerald-400`<br>Fail: 🔴 `text-red-400` (漫頂越浪)[cite: 7] |

---

## 4. 空間地理坐標、實體海圖與極端天候因性同化規範

### 4.1 精準水域地理坐標錨定
為確保海圖視覺化絕對精準，坐標必須精確錨定於外海水域，嚴禁偏移至陸地中心[cite: 22]：
- **北岸碼頭 (North Pier)**：`[24.8437, 121.9438]`（北側引道外緣水域，標高 +3.20m CD / 拋石水深 -3.20m CD）[cite: 2, 22]。
- **南岸碼頭 (South Pier)**：`[24.8415, 121.9425]`（龜尾湖南側突堤泊位水面，標高 +2.50m CD / 浚挖水深 -5.50m CD）
