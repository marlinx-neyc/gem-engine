# GEM-ENG-SPEC-2026-V43: 龜山島海事戰術動態調和系統工程規範

**密級標籤：** 生產級核心技術規範 (Production Standard)
**生效日期：** 2026-10-13
**適用範圍：** 龜山島海域客輪航行、碼頭靠泊調度、防災應急避險與自主學習主控系統

---

## 1. 系統使命與控制論架構
本系統（GEM Engine v43.0 Master）為龜山島海事戰術指揮智庫之最高 AI 主控大腦。系統宗旨在於將《易經》「執兩用中」哲學深度轉化為約束馬可夫決策過程（CMDP），解決傳統二分法（非開即封）在灰色過渡態頻繁引發的「誤判開島」與「過度停航」問題。

*   **執兩（剛性邊界約束）：**
    *   **純乾極陽邊界（100.0% 放行）：** 環境能量完全受控，四層物理防線全數通過。
    *   **純坤極陰邊界（0.0% 熔斷）：** 遭遇港池長浪消能瓦解或水下觸底坐灘風險，一票否決觸發 Hard VETO 剛性熔斷。
*   **用中（62 卦灰色相變調和）：** 主動釋放「航速連續調控」、「雙岸空間位移」與「時域非線性截斷」三大控制自由度，維持動態平衡。

---

## 2. 立體多維物理感知與通訊規範
### 2.1 遙測與邊緣計算硬體
*   **X-band 高頻雷達：** 採樣 $\ge 10\text{Hz}$，方向解析度 $\le 2.5^\circ$。用於解算波能譜，當 $T_p \ge 12.0\text{s}$ 或低頻能量 $> 35\%$ 時，消能因子 $K_d = 1.00$。
*   **AIS-GEBCO 載具雙生模組：** Class A 更新週期 $\le 2.0\text{s}$。動態淺水蹲沉方程：
    *   $F_h = \min\left(0.95, \frac{V_{speed} \cdot 0.5144}{\sqrt{g \cdot d_{chart}}}\right)$
    *   $S_{squat} = \frac{C_B \cdot V_{speed}^2}{30 \cdot (d_{chart}/d_{draft})} \cdot \frac{1}{\sqrt{\max(0.05, 1 - F_h^2)}} \cdot 0.50$
*   **Vision-PINN 邊緣光學儀：** 幀率 $\ge 30\text{FPS}$。偵測越浪率 $CV > 0.0\text{ p/min}$ 時，100ms 內覆寫預留乾舷 $FB = 0.15\text{m}$。
*   **雙岸差分氣象儀：** 解算掩蔽係數 $K_w$。$\Delta\theta < 35^\circ$ 且南岸受風 $K_w = 0.78$；$35^\circ \le \Delta\theta < 45^\circ$ 時 $K_w = 0.88$；$\Delta\theta \ge 45^\circ$ 時 $K_w = 1.00$。

---

## 3. 四層剛性物理防線 (Hard VETO Physics Matrix)
嚴格執行一票否決：$\text{Hard\_Veto} = \text{Veto}_{Hs} \lor \text{Veto}_{W} \lor \text{Veto}_{UKC} \lor \text{Veto}_{FB}$

1.  **太陽(波能)：** 港池折算波高 $H_{s,pier} \le 1.13\text{ m}$。若 $T_p \ge 12.0\text{ s}$ 則 $K_d = 1.00$。
2.  **少陽(風能)：** 攻角有效風速 $W_{eff} \le 10.17\text{ m/s}$。
3.  **少陰(底阻)：** 動態安全裕深 $UKC = (d_{chart} + \eta_{tide}) - (d_{draft} + S_{squat}) - H_{s,pier} \ge 1.50\text{ m}$。
4.  **太陰(頂阻)：** 預留乾舷高程 $FB_{pier} = 3.20\text{ m} - \eta_{tide} \ge 0.50\text{ m}$。越浪覆寫機制優先。

---

## 4. 全域能量張量與決策坍縮
*   **兩儀動能阻抗平衡：** $\mathcal{E}_{net} = \frac{H_{s,pier} + (W_{eff} \cdot 0.1) + S_{squat}}{0.5 \cdot UKC + 0.5 \cdot FB_{pier}}$
*   **Fermi-Dirac 算子：** $P_{veto} = \frac{1}{1 + \exp\left( -\frac{\mathcal{E}_{net} - 1.00}{0.25 \cdot \alpha_{tune}} \right)}$
    *   $P_{veto} < 0.20$：常態開放 (Action 2)。
    *   $P_{veto} > 0.80$：剛性熔斷 (Action 0)。
    *   $0.20 \le P_{veto} \le 0.80$：灰色過渡帶 (啟動 Action 1 或 Action 3)。

---

## 5. YZ-RL 雙 Q 強化學習引擎
*   **PER Buffer：** 容量 3000，優先級依賴 TD-Error。
*   **Reward Matrix：**
    *   Action 1 (移防南岸 + 限速 3 節) / Action 0 (正確避險)：$+18.0$
    *   Action 3 (動態開窗及時撤離) / Action 2 (常態通航)：$+16.0$
    *   盲目冒進 (觸底/長浪共振)：$-35.0$
    *   過度停航誤封：$-20.0$
*   **態互蒸餾器標準：** 常態海況歷史吻合度需達 93.8% ~ 95.0%。極端海況底線 $\ge 75.0\%$。

---

## 6. 現場戰術調度與應急規範
*   **Action 0 (🔴 VETO)：** $0.0\text{ kts}$，全線封島。
*   **Action 1 (🟡 Q2)：** 強制 $\le 3.0\text{ kts}$ (消除蹲沉)，移防南岸。
*   **Action 2 (🟢 Q1)：** 常規 $\le 12.0\text{ kts}$，北岸主泊位。
*   **Action 3 (⏱️ Q3)：** 謹慎 $\le 8.0\text{ kts}$，北岸限時泊位。**11:20 剛性止登 / 14:20 強制全員清島撤離**。
*   **避難撤離精算：** $Evac\_Min = \left\lceil \frac{Pax}{10} + \max(0.0, (S_{squat} - 0.50) \cdot 15.0) + 5.0 \right\rceil$。撤離航向 $245^\circ \text{ WSW}$ 直航烏石港。
*   **牛奶海避險：** 滿潮 $+ 3.5\text{h}$ 極值。滿潮後 $2.0 \sim 5.0\text{h}$ 區間全域禁下水，戒護線外推 $200\text{m}$。
