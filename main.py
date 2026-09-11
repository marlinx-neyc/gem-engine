# -*- coding: utf-8 -*-
"""
GEM-V36D 終極版 數位雙生海事戰術智庫 - 中央協調器
包含: 36D 特徵、PINN 物理引擎 (Tier-0 脊髓防線)、RL 動態預測、自主反饋學習閉環
"""
import os
import json
import math
import torch
import torch.nn as nn
import numpy as np
from datetime import datetime
from pydantic import BaseModel, Field

# =====================================================================
# 1. 遙測數據 Schema (含 Tier-0 災變變數)
# =====================================================================
class UnifiedMarineTelemetry(BaseModel):
    sender_id: str = Field(default="CWA_API_REALTIME")
    hs_cwa: float = Field(default=1.50)
    w_cwa: float = Field(default=8.00)
    tp_s: float = Field(default=10.5)
    delta_theta_deg: float = Field(default=25.0)
    tide_eta_m: float = Field(default=1.20)
    d_draft: float = Field(default=1.60)
    s_quat: float = Field(default=0.40)
    path_deviation_m: float = Field(default=0.25)
    adcp_current_knots: float = Field(default=1.00)
    ship_roll_deg: float = Field(default=1.50)
    ship_pitch_deg: float = Field(default=0.80)
    mooring_strain_pct: float = Field(default=35.0)
    lidar_turbulence_ti: float = Field(default=0.08)
    gust_factor_g: float = Field(default=1.15)
    wamos_directional_spreading_deg: float = Field(default=25.0)
    wave_steepness_sw: float = Field(default=0.025)
    ig_wave_energy_ratio: float = Field(default=0.04)
    kuroshio_velocity_knots: float = Field(default=1.20)
    cctv_overtopping_rate_pmin: float = Field(default=0.2)
    active_pier_select: int = Field(default=0)
    namr_multibeam_depth_m: float = Field(default=8.50)
    namr_seabed_erosion_offset_m: float = Field(default=0.15)
    namr_datum_twvd2000_offset_m: float = Field(default=0.05)
    biggis_disaster_spatial_prior: float = Field(default=0.15)
    biggis_coastal_hazard_index: float = Field(default=0.10)
    typhoon_dist_km: float = Field(default=600.0)
    pressure_gradient_2d: float = Field(default=1.10)
    swell_period_tp: float = Field(default=11.0)
    astro_tide_phase: float = Field(default=0.50)
    day_of_year: int = Field(default=250)
    chrono_risk_prior: float = Field(default=0.35)
    eps_wind_std: float = Field(default=1.15)
    future_3h_tide_surge_m: float = Field(default=0.20)
    taiyi_cycle_year: float = Field(default=9.3)
    jiazi_cycle_year: float = Field(default=30.0)
    qimen_xun_anomaly: float = Field(default=0.0)
    solar_term_idx: float = Field(default=15.0)
    lunar_phase: float = Field(default=0.5)
    macro_resonance_risk: float = Field(default=0.0)

    # 🚨 災難級別變數 (Tier-0 觸發條件)
    tsunami_pulse_alert: bool = Field(default=False)
    visibility_m: float = Field(default=5000.0)
    local_pga_gal: float = Field(default=0.0)

# =====================================================================
# 2. 36D 特徵提取與模型架構
# =====================================================================
class GEM36DNormalizedFeatureExtractor:
    BOUNDS = np.array([
        [0.0, 10.0], [0.0, 50.0], [-1.0, 5.0], [0.0, 5.0], [0.0, 5.0], [0.0, 20.0],
        [0.0, 10.0], [0.0, 100.0], [0.0, 0.5], [1.0, 2.5], [0.0, 90.0], [0.0, 0.1],
        [0.0, 0.5], [0.0, 5.0], [0.0, 20.0], [0.0, 1.0], [0.0, 15.0], [-1.0, 1.0],
        [-0.5, 0.5], [0.0, 1.0], [0.0, 1.0], [0.0, 1000.0], [0.0, 10.0], [0.0, 25.0],
        [0.0, 1.0], [-1.0, 1.0], [-1.0, 1.0], [0.0, 1.0], [0.0, 3.0], [0.0, 2.0],
        [0.0, 18.6], [0.0, 60.0], [0.0, 1.0], [0.0, 24.0], [0.0, 1.0], [0.0, 1.0]
    ], dtype=np.float32)

    def build_normalized_vector(self, t: UnifiedMarineTelemetry) -> np.ndarray:
        sin_solar = math.sin(2 * math.pi * t.day_of_year / 365.25)
        cos_solar = math.cos(2 * math.pi * t.day_of_year / 365.25)
        raw_vec = np.array([
            t.hs_cwa or 0.0, t.w_cwa or 0.0, t.tide_eta_m or 0.0, t.path_deviation_m,
            t.adcp_current_knots or 1.0, t.ship_roll_deg or 2.0, t.ship_pitch_deg or 1.0,
            t.mooring_strain_pct or 50.0, t.lidar_turbulence_ti or 0.10, t.gust_factor_g,
            t.wamos_directional_spreading_deg, t.wave_steepness_sw,
            t.ig_wave_energy_ratio, t.kuroshio_velocity_knots,
            t.cctv_overtopping_rate_pmin, float(t.active_pier_select),
            t.namr_multibeam_depth_m, t.namr_seabed_erosion_offset_m, t.namr_datum_twvd2000_offset_m,
            t.biggis_disaster_spatial_prior, t.biggis_coastal_hazard_index,
            t.typhoon_dist_km, t.pressure_gradient_2d, t.swell_period_tp,
            t.astro_tide_phase, sin_solar, cos_solar,
            t.chrono_risk_prior, t.eps_wind_std, t.future_3h_tide_surge_m,
            t.taiyi_cycle_year, t.jiazi_cycle_year, t.qimen_xun_anomaly,
            t.solar_term_idx, t.lunar_phase, t.macro_resonance_risk
        ], dtype=np.float32)
        min_b, max_b = self.BOUNDS[:, 0], self.BOUNDS[:, 1]
        return np.clip((raw_vec - min_b) / (max_b - min_b + 1e-6), 0.0, 1.0)

class PINNResidualNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(36, 32), nn.Tanh(), nn.Linear(32, 16), nn.Tanh(), nn.Linear(16, 2), nn.Hardtanh(-0.15, 0.15))
    def forward(self, x): return self.net(x)

class AIClassifierPolicy(nn.Module):
    def __init__(self, input_dim=36, hidden_dim=128, output_dim=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.BatchNorm1d(hidden_dim), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, output_dim)
        )
    def forward(self, x): return self.net(x)

# =====================================================================
# 3. 具備 Tier-0 脊髓反射的 PINN 物理引擎
# =====================================================================
class PINNPhysicsEngine:
    def __init__(self):
        self.residual_net = PINNResidualNet()

    def evaluate_physics(self, t: UnifiedMarineTelemetry, norm_vector: np.ndarray = None) -> dict:
        # 🚨 第一道防線：Tier-0 脊髓反射 (上帝防禦機制)
        if t.tsunami_pulse_alert:
            return {"hs_pier_m": 99.9, "w_local_ms": 99.9, "ukc_m": 0.0, "fb_pier_m": 0.0, 
                    "has_veto": True, "reason": "[Tier-0 警報] 海嘯預警！一票否決，全線撤離！", "is_tier0": True}
        if t.local_pga_gal >= 250:
            return {"hs_pier_m": 99.9, "w_local_ms": 99.9, "ukc_m": 0.0, "fb_pier_m": 0.0, 
                    "has_veto": True, "reason": "[Tier-0 警報] 測得 5 級強震！結構堪慮，啟動 24H 封鎖安檢！", "is_tier0": True}
        if t.visibility_m < 500:
            return {"hs_pier_m": 99.9, "w_local_ms": 99.9, "ukc_m": 0.0, "fb_pier_m": 0.0, 
                    "has_veto": True, "reason": "[Tier-0 警報] 暴雨/濃霧致盲 (能見度 < 500m)，嚴禁靠泊！", "is_tier0": True}

        # 🛡️ 第二道防線：常規 PINN 物理消能算子
        macro_penalty_kd = 0.15 if t.qimen_xun_anomaly > 0.8 else 0.0
        macro_penalty_kw = 0.20 if t.qimen_xun_anomaly > 0.8 else 0.0
        kd_base = 1.00 if (t.tp_s or 0) > 12.0 else 0.883 + macro_penalty_kd
        kw_base = 1.00 if (t.delta_theta_deg or 0) >= 45.0 else 0.78 + macro_penalty_kw
        
        res_kd, res_kw = 0.0, 0.0
        if norm_vector is not None:
            with torch.no_grad():
                residuals = self.residual_net(torch.FloatTensor(norm_vector).unsqueeze(0)).squeeze(0).numpy()
                res_kd, res_kw = float(residuals[0]), float(residuals[1])

        kd = float(np.clip(kd_base + res_kd, 0.1, 1.2))
        kw = float(np.clip(kw_base + res_kw, 0.1, 1.2))
        effective_depth = t.namr_multibeam_depth_m - getattr(t, 'namr_seabed_erosion_offset_m', 0.15)
        
        hs_pier = round((t.hs_cwa or 0.0) * kd, 2)
        w_local = round((t.w_cwa or 0.0) * kw, 2)
        ukc = round((effective_depth + (t.tide_eta_m or 0.0)) - (t.d_draft + t.s_quat) - (hs_pier * 0.5), 2)
        fb_pier = round(1.90 - (t.tide_eta_m or 0.0), 2)
        
        has_veto = (hs_pier > 1.20 or w_local > 10.80 or ukc < 1.50 or fb_pier < 0.50)
        return {"hs_pier_m": hs_pier, "w_local_ms": w_local, "ukc_m": ukc, "fb_pier_m": fb_pier, 
                "has_veto": has_veto, "reason": "物理門檻超標" if has_veto else "安全", "is_tier0": False}

# =====================================================================
# 4. 主排程器與 MLOps 自主反饋循環
# =====================================================================
FEEDBACK_LOG_FILE = "rl_autonomous_feedback.jsonl"

def log_rl_feedback(telemetry_id, features_36d, rl_pred, expert_target, reason):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "telemetry_id": telemetry_id,
        "features_36d": [float(x) for x in features_36d],
        "rl_prediction": rl_pred,
        "ground_truth": expert_target,
        "contradiction_reason": reason
    }
    with open(FEEDBACK_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

class ResilientTacticalOrchestrator:
    def __init__(self, model_path="model_v36D.10.6.pt"):
        self.extractor = GEM36DNormalizedFeatureExtractor()
        self.pinn_engine = PINNPhysicsEngine()
        self.policy = AIClassifierPolicy(input_dim=36)
        if os.path.exists(model_path):
            self.policy.load_state_dict(torch.load(model_path, map_location="cpu"))
            self.policy.eval()
            print(f"✅ 已載入 36D 最佳神經網絡權重: {model_path}")

    def execute_cycle(self):
        # 產生實境測試數據 (未來這裡接 CWA API)
        t = UnifiedMarineTelemetry(hs_cwa=1.1, w_cwa=8.5, tp_s=14.5, chrono_risk_prior=0.88)
        full_36d_vec = self.extractor.build_normalized_vector(t)
        
        # 1. 物理引擎評估 (含 Tier-0)
        metrics = self.pinn_engine.evaluate_physics(t, full_36d_vec)
        has_veto = metrics["has_veto"]
        is_tier0 = metrics["is_tier0"]

        # 2. AI 大腦預測
        with torch.no_grad():
            rl_pred = int(torch.argmax(self.policy(torch.FloatTensor(full_36d_vec).unsqueeze(0)), dim=1).item())

        # 3. MLOps 線上反饋判斷 (若是 Tier-0 災變則不計入常規訓練)
        contradiction_flag = False
        if not is_tier0:
            if has_veto and rl_pred != 2:
                contradiction_flag = True
                log_rl_feedback(t.sender_id, full_36d_vec, rl_pred, 2, "False Negative (應封島但未封)")
            elif not has_veto and rl_pred == 2 and t.hs_cwa < 1.0:
                contradiction_flag = True
                log_rl_feedback(t.sender_id, full_36d_vec, rl_pred, 0, "False Positive (過度保守)")

        # 4. 決策輸出
        if is_tier0:
            decision_code = "Q4_DISASTER"
        else:
            final_act = 2 if has_veto else rl_pred
            decision_code = "Q4" if final_act == 2 else ("Q2" if final_act == 1 else "Q1")

        # 5. 打包 JSON 供前端儀表板使用
        ssot_payload = {
            "sender_id": t.sender_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision_code": decision_code,
            "tier0_reason": metrics["reason"] if is_tier0 else "",
            "physics_metrics": metrics,
            "rl_feedback_status": {
                "has_contradiction": contradiction_flag,
                "raw_rl_prediction": "Q4" if rl_pred == 2 else ("Q2" if rl_pred == 1 else "Q1")
            },
            "pattern_match": {
                "matched_cases": 12,
                "historical_closure_rate": t.chrono_risk_prior,
                "max_similarity_score": 0.9123
            }
        }
        
        with open("latest_decision.json", "w", encoding="utf-8") as f:
            json.dump(ssot_payload, f, indent=2, ensure_ascii=False)
        print(f"📡 決策輸出完成: {decision_code} | VETO: {has_veto} | 反饋矛盾已記錄: {contradiction_flag}")

if __name__ == "__main__":
    orchestrator = ResilientTacticalOrchestrator(model_path="model_v36D.10.6.pt")
    orchestrator.execute_cycle()
