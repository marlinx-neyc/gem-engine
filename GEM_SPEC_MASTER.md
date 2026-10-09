# GEM_SPEC_MASTER.md
# GEM-V36D 龜山島數位雙生海事戰術控制台暨 AI 專家顧問最高技術規格檔

**文件版本**：v36D.340 Complete Advisory & Master Autonomous Edition  
**生效日期**：2026-10-09  
**適用範疇**：後端 Python / UKF / PINN 算子、SSOT `latest_decision.json` 封包、Desktop/Mobile UI Canvas 介面、GEM AI 專家顧問檢核引擎與 Notion DB 數位存根。

---

## 1. 系統架構、SSOT 合約與 GEM AI 顧問檢核機制

### 1.1 專家顧問角色與數據檢核合約 (Advisory Contract)
1. **GEM AI 專家顧問定位**：統合「海洋工程學、氣象學、觀光景區營運、周易象數與 Reinforcement Learning」五大領域，擔任龜山島海域水文實測與戰術調度之最高檢核與裁決機制。
2. **單一真實數據源 (SSOT)**：
   - 後端由 `main_orchestrator.py` 與 10 秒級排程產出唯一數據源，寫入 `latest_decision.json`[cite: 22]。
   - 前端（`desktop.html`, `mobile.html`）與 GEM AI 顧問為消費者，強制採納 JSON 數據作為 Ground Truth[cite: 22]。
3. **數據檢核與 ACK 握手協定**：
   - GEM 顧問在生成任何報告前，必須對 telemetry 發起 4 層物理防線檢核：
     $$\text{Audit\_Pass} = \left( H_{s,pier} \le 1.13 \right) \land \left( W_{eff} \le 10.17 \right) \land \left( UKC \ge 1.50 \right) \land \left( FB_{pier} \ge 0.50 \right)$$
   - 若 $\text{Audit\_Pass} = \text{False}$，強制將狀態標記為 `🔴 0.0% 物理 VETO 熔斷`，並產出權威總裁示。

---

## 2. 微觀水動力四層物理防線與剛性熔斷算子

### 2.1 四層剛性算子精算矩陣

| 算子名稱 | 符號 | 精算公式 / 遲滯函數 | 剛性檢核通過門檻 | 燈號與字色表現 |
| :--- | :--- | :--- | :--- | :--- |
| **碼頭有效波高** | $H_{s,pier}$ | $H_{s,pier} = H_{s,CWA} \cdot K_d(T_p) + PINN_{offset}$<br>若 $T_p > 12.0\text{s} \implies K_d = 1.00$ (長浪擊穿) | $H_{s,pier} \le 1.20 \cdot \alpha_{tune}\text{ m}$<br>($\alpha=0.94 \implies 1.13\text{m}$) | Pass: 🟢 `text-emerald-400`<br>Fail: 🔴 `text-red-400` |
| **攻角有效風速** | $W_{eff}$ | $W_{eff} = W_{local} \cdot \vert{}\cos(\Delta\theta)\vert{} \cdot K_w$<br>若 $\Delta\theta \ge 45^\circ \implies K_w = 1.00$ | $W_{eff} \le 10.80 \cdot \alpha_{tune}\text{ m/s}$<br>($\alpha=0.94 \implies 10.17\text{m/s}$) | Pass: 🟢 `text-emerald-400`<br>Fail: 🔴 `text-red-400` |
| **動態富餘水深** | $UKC$ | $UKC = (d_{chart} + \eta_{tide}) - (d_{draft} + S_{squat}) - H_{s,pier}$<br>含客輪吃水 1.20m + 雙體船蹲沉 $S_{squat}=0.82\text{m}$ (共 2.02m) | $UKC \ge 1.50\text{ m}$<br>(北岸基底-3.2m / 南岸浚挖-5.5m) | Pass: 🟢 `text-emerald-400`<br>Warn: 🟡 `text-amber-300`<br>Fail: 🔴 `text-red-400` (坐灘/觸底) |
| **預留乾舷高程** | $FB_{pier}$ | $FB_{pier} = BASE\_FREEBOARD - \eta_{tide}$<br>若 Vision-PINN 越浪率 $CV > 0\text{ p/min} \implies FB_{pier} = 0.15\text{ m}$ | $FB_{pier} \ge 0.50\text{ m}$ | Pass: 🟢 `text-emerald-400`<br>Fail: 🔴 `text-red-400` (漫頂) |

---

## 3. 核心 UI 元件、視覺圖表與極簡排版規範

### 3.1 五大關鍵安全裕度雙岸動態儀表 (Dual-Sided Bullet Gauge)
- **視覺原則**：徹底淘汰冗長純文字表格，整合為 5 大物理防線（①波高 $H_s$、②裕深 $UKC$、③乾舷 $FB$、④攻角風 $W_{eff}$、⑤消能 $K_d \cdot K_w$）。
- **雙岸對稱結構**：左欄為【北岸碼頭】，右欄為【南岸碼頭】，中央標記 100% 剛性安全臨界線。
- **動態響應**：長度、超標百分比、文字字色與燈號徽章隨沙盤滑桿即時平滑計算。

### 3.2 🎯 全維度戰術安全態勢雷達圖 (Radar Chart Specification)
- **維度端點 (6 軸)**：$H_s$ 浪高、$W_{eff}$ 攻角風、$T_p$ 湧浪週期、$UKC$ 裕深、$FB$ 乾舷、$CV$ 越浪率。
- **三向分頁切換**：
  - `⚓ 南岸碼頭`：綠色多邊形，聚焦 -5.5m CD 浚挖水深與 UKC 觸底危險。
  - `⚓ 北岸碼頭`：天藍多邊形，聚焦 -3.2m CD 拋石基底、迎風蓋頂與坐灘破底。
  - `⚖️ 雙岸疊合`：紫/綠雙多邊形同屏疊合比對。
- **畫布邊界鉗位保護**：`cy = h * 0.46`，底端 `UKC` 坐標加上 `Math.min(h - 18, ...)` 保護，杜絕下邊文字裁切。

### 3.3 🚢 船班航次動態時序剖面圖 (Schedule-Driven Bathymetry Profile)
- **時段控制列**：支援 `08:00 首班`、`10:00 滿潮`、`11:20 止登`、`12:00 風變`、`14:20 撤離`、`16:00 末班` 與「▶ 自動輪播推演」。
- **左右方位嚴格對齊**：
  - 畫布左半部標記 `⚓ 北岸碼頭 (+3.2m CD / -3.2m 拋石)` 🠮 對齊下方左側北岸說明卡片。
  - 畫布右半部標記 `⚓ 南岸碼頭 (+2.5m CD / -5.5m 浚挖)` 🠮 對齊下方右側南岸說明卡片。
- **懸浮感應 (Hover Tooltip)**：南/北岸水體全域感應（$x \in [\text{midX}, \text{pierX}]$, $y \in [y_{tide}, y_{bed}]$），浮動顯示：`時段節點 + 實測vs限值比對 + 燈號標籤 + 戰術處置`。

---

## 4. 碼頭名稱動態角色指派與時程避險演算法

### 4.1 碼頭簡化與動態角色指派演算法 (Dynamic Role Assignment)
```python
def assign_pier_roles(delta_theta_deg, pass_north, pass_south):
    if pass_north and pass_south:
        if delta_theta_deg < 35.0:
            return {"north": "主要泊位 🟢", "south": "備用權宜 🟢"}
        else:
            return {"north": "備用權宜 🟢", "south": "主要泊位 🟢"}
    elif pass_south and not pass_north:
        return {"north": "迎風失效 🔴", "south": "背風主要靠泊 🟢"}
    elif pass_north and not pass_south:
        return {"north": "主要泊位 🟢", "south": "淺水失效 🔴"}
    else:
        return {"north": "雙岸失效 (全線封島) 🔴", "south": "雙岸失效 (全線封島) 🔴"}
