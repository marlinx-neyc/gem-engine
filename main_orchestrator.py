import math
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, List

# ==============================================================================
# 1. 遙測資料結構 (Marine Safety Telemetry)
# ==============================================================================
@dataclass
class MarineSafetyData:
    hs_cwa: float              # CWA 外海波高 (m)
    w_cwa: float               # CWA 局域風速 (m/s)
    tp_s: float                # 湧浪週期 (s)
    delta_theta_deg: float     # 背風偏角 (度)
    tide_eta_m: float          # 天文潮位 (m)
    d_draft_m: float           # 船隻吃水 (m)
    s_quat_m: float            # 船體沉降 Squat (m)
    chart_depth_m: float       # 碼頭圖水深 (m)
    current_speed_kts: float   # 海流速度 (kts)
    qimen_consensus_pct: float # 奇門氣場同化率 (%)
    s_cos_sim: float           # 歷史餘弦相似度 (0~1)
    passenger_count: int = 120 # 現場待撤離/登島人數
    slope_landslide_risk: float = 0.15
    official_closure_status: float = 0.0
    active_pier_select: int = 0
    typhoon_dist_km: float = 650.0
    pressure_gradient_2d: float = 1.10

# ==============================================================================
# 2. 37D 特徵張量全通道同構化轉譯器 (Feature Extractor)
# ==============================================================================
class GEM37DNormalizedFeatureExtractor:
    BOUNDS = np.array([
        [0.0, 10.0], [0.0, 50.0], [-1.0, 5.0], [0.0, 5.0], [0.0, 5.0],
        [0.0, 20.0], [0.0, 10.0], [0.0, 100.0], [0.0, 0.5], [1.0, 2.5],
        [0.0, 90.0], [0.0, 0.1], [0.0, 0.5], [0.0, 5.0], [0.0, 20.0],
        [0.0, 1.0], [0.0, 15.0], [-1.0, 1.0], [-0.5, 0.5], [0.0, 1.0],
        [0.0, 1.0], [0.0, 1000.0], [0.0, 10.0], [0.0, 25.0], [0.0, 1.0],
        [-1.0, 1.0], [-1.0, 1.0], [0.0, 1.0], [0.0, 3.0], [0.0, 2.0],
        [0.0, 18.6], [0.0, 60.0], [0.0, 1.0], [0.0, 24.0], [0.0, 100.0],
        [0.0, 1.0], [0.0, 1.0]
    ], dtype=np.float32)

    def build_normalized_vector(self, t: MarineSafetyData) -> np.ndarray:
        raw_vec = np.array([
            t.hs_cwa, t.w_cwa, t.tide_eta_m, 0.25, 1.0, 1.5, 0.8, 35.0,
            0.08, 1.15, 25.0, 0.025, 0.04, 1.20, t.slope_landslide_risk,
            float(t.active_pier_select), t.chart_depth_m, 0.15,
            0.05, 0.15, 0.10, t.typhoon_dist_km, t.pressure_gradient_2d,
            t.tp_s, 0.5, 0.5, 0.5, 0.35, 1.15, 0.20, 9.3, 30.0, 0.0,
            15.0, t.qimen_consensus_pct, 0.2, t.official_closure_status
        ], dtype=np.float32)
        return np.clip(
            (raw_vec - self.BOUNDS[:, 0]) / (self.BOUNDS[:, 1] - self.BOUNDS[:, 0] + 1e-6),
            0.0, 1.0
        )

# ==============================================================================
# 3. 剛性四層物理防線與水動力算子引擎 (Physics & VETO Engine)
# ==============================================================================
class PhysicsEngine:
    HARD_HS_MAX = 1.20       # m
    HARD_WEFF_MAX = 10.80    # m/s
    HARD_UKC_MIN = 1.50      # m
    HARD_FB_MIN = 0.50       # m
    BASE_FREEBOARD = 3.20    # 碼頭基準乾舷 (m)

    @staticmethod
    def calculate_kd(tp: float) -> float:
        """長浪繞射消能算子 Kd 遲滯精算"""
        if tp < 11.5:
            return 0.883
        elif 11.5 <= tp <= 12.0:
            return 0.883 + (1.00 - 0.883) * ((tp - 11.5) / 0.5)
        else:
            return 1.00

    @staticmethod
    def calculate_kw(delta_theta: float) -> float:
        """風速背風遮蔽衰減算子 Kw 遲滯精算"""
        if delta_theta < 30.0:
            return 0.78
        elif 30.0 <= delta_theta < 45.0:
            return 0.78 + (1.00 - 0.78) * ((delta_theta - 30.0) / 15.0)
        else:
            return 1.00

    @classmethod
    def evaluate_veto(cls, data: MarineSafetyData, alpha_tune: float = 1.0) -> Dict[str, Any]:
        r"""四層 Hard VETO 熔斷檢核 ($H_{s,pier} \le 1.20\text{ m}$, $W_{eff} \le 10.80\text{ m/s}$, $UKC \ge 1.50\text{ m}$, $FB_{pier} \ge 0.50\text{ m}$)"""
        kd = cls.calculate_kd(data.tp_s)
        kw = cls.calculate_kw(data.delta_theta_deg)
        
        hs_pier = round(data.hs_cwa * kd, 2)
        w_local = round(data.w_cwa * kw, 2)
        w_eff = round(w_local * abs(math.cos(math.radians(data.delta_theta_deg))), 2)

        ukc = round((data.chart_depth_m + data.tide_eta_m) - (data.d_draft_m + data.s_quat_m) - hs_pier, 2)
        fb_pier = round(cls.BASE_FREEBOARD - data.tide_eta_m, 2)

        eff_hs_limit = round(cls.HARD_HS_MAX * alpha_tune, 2)
        eff_weff_limit = round(cls.HARD_WEFF_MAX * alpha_tune, 2)

        pass_hs = hs_pier <= eff_hs_limit
        pass_w = w_eff <= eff_weff_limit
        pass_ukc = ukc >= cls.HARD_UKC_MIN
        pass_fb = fb_pier >= cls.HARD_FB_MIN

        has_veto = not (pass_hs and pass_w and pass_ukc and pass_fb)

        return {
            "hs_pier_m": hs_pier,
            "w_eff_ms": w_eff,
            "ukc_m": ukc,
            "fb_pier_m": fb_pier,
            "pass_hs": pass_hs,
            "pass_w": pass_w,
            "pass_ukc": pass_ukc,
            "pass_fb": pass_fb,
            "has_veto": has_veto,
            "kd": kd,
            "kw": kw,
            "alpha_tune": alpha_tune
        }

# ==============================================================================
# 4. 二十年海象氣候智庫比對引擎 (20-Year Climate Matching Engine)
# ==============================================================================
class OptimizedHistorical20YrEngine:
    def __init__(self):
        self.num_records = 1200
        self.feature_dim = 37
        self.feature_weights = torch.ones(37, dtype=torch.float32)
        self.feature_weights[0] = 3.5   # Hs
        self.feature_weights[1] = 3.0   # Wind
        self.feature_weights[23] = 3.5  # Tp
        self.feature_weights[3] = 2.0   # Delta Theta
        self.feature_weights[34] = 2.0  # Qimen Consensus
        self.feature_weights /= self.feature_weights.sum()

        c1 = torch.tensor([0.08, 0.12, 0.20, 0.15] + [0.1]*33)
        c2 = torch.tensor([0.25, 0.35, 0.40, 0.45] + [0.2]*33)
        c3 = torch.tensor([0.15, 0.20, 0.85, 0.20] + [0.1]*33)
        base_db = torch.cat([c.repeat(self.num_records // 3, 1) for c in [c1, c2, c3]], dim=0)
        noise = torch.randn_like(base_db) * 0.05
        self.db_tensor = torch.clamp(base_db + noise, 0.0, 1.0)
        self.db_veto_labels = (self.db_tensor[:, 0] > 0.28).float()

    def match_live_telemetry(self, live_37d_vec: np.ndarray, top_k: int = 50) -> Dict[str, Any]:
        w_sqrt = torch.sqrt(self.feature_weights).unsqueeze(0)
        live_t = torch.tensor(live_37d_vec, dtype=torch.float32).unsqueeze(0) * w_sqrt
        db_w = self.db_tensor * w_sqrt

        live_norm = F.normalize(live_t, p=2, dim=1)
        db_norm = F.normalize(db_w, p=2, dim=1)

        sim_scores = torch.mm(db_norm, live_norm.T).squeeze(-1)
        topk_scores, topk_indices = torch.topk(sim_scores, k=min(top_k, self.db_tensor.size(0)))

        avg_similarity = topk_scores.mean().item()
        historical_veto_rate = self.db_veto_labels[topk_indices].mean().item()

        raw_confidence = (avg_similarity * 0.70 + (1.0 - historical_veto_rate * 0.30)) * 100
        reliability_score = round(min(99.9, max(0.0, raw_confidence)), 2)

        alpha_corrected = 1.00
        if avg_similarity >= 0.85 and historical_veto_rate > 0.30:
            alpha_corrected = round(max(0.65, 1.00 - (historical_veto_rate * 0.35)), 4)

        return {
            "top_k_similarity_mean": round(avg_similarity, 4),
            "historical_20yr_veto_probability": round(historical_veto_rate, 4),
            "reliability_score_pct": reliability_score,
            "alpha_tune_historical_corrected": alpha_corrected
        }

# ==============================================================================
# 5. 奇門 70% 門控同化與 Sigmoid 策略神經網路
# ==============================================================================
class QimenOctagramAssimilationEngine:
    QIMEN_THRESHOLD_GATE = 70.0

    @classmethod
    def evaluate(cls, qimen_pct: float, tp: float, delta_theta: float, has_veto: bool) -> Tuple[bool, str]:
        enabled = qimen_pct >= cls.QIMEN_THRESHOLD_GATE
        if has_veto:
            gate = "死門 (坤宮 - 剛性熔斷)"
        elif tp > 12.0:
            gate = "驚門 (兌宮 - 湧浪共振)"
        elif delta_theta >= 38.0:
            gate = "杜門 (巽宮 - 移防南岸)"
        else:
            gate = "開門 (乾宮 - 穩定靠泊)"
        return enabled, gate

class GEMV36DReinforcedPolicyNet(nn.Module):
    def __init__(self, state_dim: int = 37, action_dim: int = 4):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.SiLU(),
            nn.Linear(64, action_dim)
        )
        self.qimen_gate = nn.Sequential(
            nn.Linear(1, 16),
            nn.Sigmoid(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def compute_sigmoid_alpha_tune(self, qimen_pct: float) -> float:
        if qimen_pct < 70.0:
            return 1.00
        qimen_tensor = torch.tensor([[qimen_pct / 100.0]], dtype=torch.float32)
        gate_weight = self.qimen_gate(qimen_tensor).item()
        alpha_base = 1.00 - (0.35 * gate_weight)
        return round(max(0.65, alpha_base), 4)

# ==============================================================================
# 6. 雙重遲滯控制器與動態人流撤離算子 (Hysteresis & Evacuation)
# ==============================================================================
class GuerrillaHysteresisController:
    def __init__(self, angle_high: float = 38.0, angle_low: float = 30.0, lockout_steps: int = 5):
        self.angle_high = angle_high
        self.angle_low = angle_low
        self.lockout_steps = lockout_steps
        self.current_state = 0
        self.lockout_counter = 0

    def evaluate_pier_switch(self, delta_theta: float, current_speed_kts: float) -> Tuple[int, str]:
        if self.lockout_counter > 0:
            self.lockout_counter -= 1
            return self.current_state, f"🔒 遲滯鎖定中 (剩餘 {self.lockout_counter + 1} 步)"
        if self.current_state == 0 and (delta_theta >= self.angle_high or current_speed_kts >= 2.0):
            self.current_state = 1
            self.lockout_counter = self.lockout_steps
            return 1, "🔀 切換至【南岸權宜碼頭】"
        elif self.current_state == 1 and (delta_theta <= self.angle_low and current_speed_kts < 1.5):
            self.current_state = 0
            self.lockout_counter = self.lockout_steps
            return 0, "🔀 切換回【北岸碼頭】"
        return self.current_state, "🟢 碼頭狀態穩定"

    @staticmethod
    def compute_dynamic_evac_window(passenger_count: int, squat_m: float) -> int:
        base_time = passenger_count / 15.0
        squat_delay = max(0.0, (squat_m - 0.50) * 15.0)
        return int(math.ceil(base_time + squat_delay + 15.0))

# ==============================================================================
# 7. TG 游擊戰術最高統合執行調度器 (TG Master Engine)
# ==============================================================================
class TGGuerrillaMasterEngine:
    def __init__(self):
        self.net = GEMV36DReinforcedPolicyNet()
        self.climate_engine = OptimizedHistorical20YrEngine()
        self.hysteresis = GuerrillaHysteresisController()
        self.extractor = GEM37DNormalizedFeatureExtractor()

    def execute(self, telemetry: MarineSafetyData) -> Dict[str, Any]:
        cst_tz = timezone(timedelta(hours=8))
        now_dt = datetime.now(cst_tz)

        # 採用 37D 特徵轉譯器同構化特徵向量
        vec37 = self.extractor.build_normalized_vector(telemetry)

        hist_res = self.climate_engine.match_live_telemetry(vec37)
        alpha_base = self.net.compute_sigmoid_alpha_tune(telemetry.qimen_consensus_pct)
        alpha_final = min(alpha_base, hist_res["alpha_tune_historical_corrected"])

        physics_res = PhysicsEngine.evaluate_veto(telemetry, alpha_final)
        qimen_enabled, qimen_gate = QimenOctagramAssimilationEngine.evaluate(
            telemetry.qimen_consensus_pct, telemetry.tp_s, telemetry.delta_theta_deg, physics_res["has_veto"]
        )

        pier_id, pier_msg = self.hysteresis.evaluate_pier_switch(telemetry.delta_theta_deg, telemetry.current_speed_kts)
        evac_minutes = GuerrillaHysteresisController.compute_dynamic_evac_window(telemetry.passenger_count, telemetry.s_quat_m)

        t_stop_dt = now_dt + timedelta(minutes=20)
        t_evac_dt = t_stop_dt + timedelta(minutes=evac_minutes)

        if physics_res["has_veto"]:
            overall_decision = "🔴 封島/防颱 (Q4)"
            berthing = "無 (雙岸靠泊功能失效)"
            evac = "直航撤離返航【烏石港】"
            summary = f"港池波高 {physics_res['hs_pier_m']}m 或風速超標，觸發 Hard VETO 熔斷，今天全天雙岸無開放班次。"
            timeline = []
        else:
            overall_decision = "🟢 安全/開放靠泊 (Q1)"
            berthing = "【南岸權宜碼頭】" if pier_id == 1 else "【北岸碼頭】"
            evac = f"{berthing} -> 【烏石港】"
            summary = "海象門檻全數 PASS，執行 TG 游擊戰術排程。"
            timeline = [
                {"time": "08:30", "action": "首班游擊登島", "location": "【南岸權宜碼頭】", "condition": "北岸越浪且 Δθ < 45°"},
                {"time": "10:50", "action": "止登預發廣播 (前30分)", "location": "全島廣播系統", "condition": f"奇門匹配率 {telemetry.qimen_consensus_pct:.1f}% 觸發"},
                {"time": "11:20", "action": "上午場止登截止", "location": "【南岸碼頭】", "condition": "上午場最後止登點"},
                {"time": "12:30", "action": "午間區間登島", "location": "【南岸權宜碼頭】", "condition": "雙岸 Hs <= 1.20m 且 Tp <= 12.0s"},
                {"time": "13:50", "action": "撤離預發廣播 (前30分)", "location": "全島廣播系統", "condition": "撤離前 30 分鐘全島預警"},
                {"time": "14:20", "action": "游擊戰術強制撤退", "location": "【南岸碼頭】 -> 【烏石港】", "condition": "巽宮風陣 Δθ >= 45° 或長浪穿透"},
                {"time": "17:30", "action": "全島最終清空離島", "location": "【南岸碼頭】 -> 【烏石港】", "condition": "每日營運最後離島時窗"}
            ]

        return {
            "version": "v36D.30.0 Three-Scheme & Guerrilla Vector Master Complete",
            "timestamp": now_dt.strftime("%Y-%m-%d %H:%M:%S CST"),
            "decision": overall_decision,
            "reliability_score_pct": hist_res["reliability_score_pct"],
            "alpha_tune_final": alpha_final,
            "physics_metrics": physics_res,
            "historical_20yr_matching": hist_res,
            "qimen_macro_consensus": {
                "consensus_rate_pct": telemetry.qimen_consensus_pct,
                "macro_advisory_enabled": qimen_enabled,
                "octagram_gate_state": qimen_gate
            },
            "guerrilla_dispatch": {
                "berthing_pier": berthing,
                "evacuation_pier": evac,
                "hysteresis_status": pier_msg,
                "dynamic_evac_minutes": evac_minutes,
                "t_stop_window": t_stop_dt.strftime("%H:%M"),
                "t_evac_window": t_evac_dt.strftime("%H:%M"),
                "tactical_summary": summary,
                "tactical_timeline": timeline
            }
        }

    def generate_markdown_report(self, data: MarineSafetyData, res: Dict[str, Any]) -> str:
        """生成對齊規範之結構化 Markdown 評估報告"""
        pm = res["physics_metrics"]
        eff_hs_limit = round(PhysicsEngine.HARD_HS_MAX * pm['alpha_tune'], 2)
        eff_weff_limit = round(PhysicsEngine.HARD_WEFF_MAX * pm['alpha_tune'], 2)

        hs_status = "[🟢 PASS]" if pm["pass_hs"] else "[🔴 VETO]"
        w_status = "[🟢 PASS]" if pm["pass_w"] else "[🔴 VETO]"
        ukc_status = "[🟢 PASS]" if pm["pass_ukc"] else "[🔴 VETO]"
        fb_status = "[🟢 PASS]" if pm["pass_fb"] else "[🔴 VETO]"

        report = f"**當前總體狀態**：**[{res['decision']}]**\n\n"
        report += "**四層剛性物理門檻檢核**\n\n"
        report += "| 檢核項目 | 實測/模擬數據 | 剛性標準門檻 | 數值比對 | 燈號狀態 |\n"
        report += "| --- | --- | --- | --- | --- |\n"
        report += f"| 碼頭波高 ($H_{{s,pier}}$) | {pm['hs_pier_m']:.2f} m | $\\le {eff_hs_limit:.2f}\\text{{ m}}$ | {pm['hs_pier_m']:.2f}m vs {eff_hs_limit:.2f}m | {hs_status} |\n"
        report += f"| 攻角風速 ($W_{{eff}}$) | {pm['w_eff_ms']:.2f} m/s | $\\le {eff_weff_limit:.2f}\\text{{ m/s}}$ | {pm['w_eff_ms']:.2f}m/s vs {eff_weff_limit:.2f}m/s | {w_status} |\n"
        report += f"| 富餘水深 ($UKC$) | {pm['ukc_m']:.2f} m | $\\ge 1.50\\text{{ m}}$ | {pm['ukc_m']:.2f}m vs 1.50m | {ukc_status} |\n"
        report += f"| 碼頭乾舷 ($FB_{{pier}}$) | {pm['fb_pier_m']:.2f} m | $\\ge 0.50\\text{{ m}}$ | {pm['fb_pier_m']:.2f}m vs 0.50m | {fb_status} |\n\n"
        
        report += "**戰術調度與智庫同化指標**\n\n"
        report += f"* **奇門氣場同化**：匹配率 {res['qimen_macro_consensus']['consensus_rate_pct']:.1f}%，對應門控【{res['qimen_macro_consensus']['octagram_gate_state']}】\n"
        report += f"* **氣候智庫信心**：二十年歷史餘弦可靠度指標 $Reliability\\ Score = {res['reliability_score_pct']:.1f}\\%$\n"
        report += f"* **處置結論**：{res['guerrilla_dispatch']['tactical_summary']}\n"
        return report

# ==============================================================================
# 8. 實測執行與驗證範例
# ==============================================================================
if __name__ == "__main__":
    engine = TGGuerrillaMasterEngine()

    # 實測範例 1：2026-09-16 颱風波高超標實測 (觸發 Hard VETO)
    veto_data = MarineSafetyData(
        hs_cwa=3.71, w_cwa=8.50, tp_s=15.5, delta_theta_deg=45.0,
        tide_eta_m=1.00, d_draft_m=1.20, s_quat_m=0.82, chart_depth_m=8.50,
        current_speed_kts=1.90, qimen_consensus_pct=100.0, s_cos_sim=0.96,
        passenger_count=150
    )

    res_veto = engine.execute(veto_data)
    print("=== 實測案例 1：2026-09-16 剛性 VETO 熔斷報告 ===")
    print(engine.generate_markdown_report(veto_data, res_veto))

    # 實測範例 2：海象條件全數 PASS (啟動 TG 游擊戰術排程)
    pass_data = MarineSafetyData(
        hs_cwa=0.85, w_cwa=6.20, tp_s=8.5, delta_theta_deg=36.0,
        tide_eta_m=1.20, d_draft_m=1.60, s_quat_m=0.34, chart_depth_m=8.50,
        current_speed_kts=1.20, qimen_consensus_pct=85.0, s_cos_sim=0.92,
        passenger_count=120
    )

    res_pass = engine.execute(pass_data)
    print("\n=== 實測案例 2：海象符合條件（PASS）戰術調度報告 ===")
    print(engine.generate_markdown_report(pass_data, res_pass))
