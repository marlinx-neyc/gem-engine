# -*- coding: utf-8 -*-
"""
GEM-V36D Dialectical Engine (v36D.11.0 雙核辯證學習引擎)
特色：
1. 微觀物理 (Micro-Physics) 與 宏觀奇門 (Macro-Qimen) 雙核並行。
2. 注意力機制 (Attention Gate) 動態分配權重。
3. 相對精確度收斂 (Precision Convergence) 與 VETO 物理防線。
"""
import os
import math
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from pydantic import BaseModel, Field

# ==============================================================================
# 1. 遙測 Schema 與 36D 特徵歸一化
# ==============================================================================
class UnifiedMarineTelemetry(BaseModel):
    sender_id: str = Field(default="CWA_API_REALTIME")
    hs_cwa: float = Field(default=3.23)
    w_cwa: float = Field(default=13.50)
    tp_s: float = Field(default=14.5)
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
    
    # === 以下為時空與奇門特徵 (Macro-Qimen) ===
    biggis_coastal_hazard_index: float = Field(default=0.10)
    typhoon_dist_km: float = Field(default=450.0)
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
    tsunami_pulse_alert: bool = Field(default=False)
    visibility_m: float = Field(default=5000.0)
    local_pga_gal: float = Field(default=0.0)

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

# ==============================================================================
# 2. 雙核神經網絡與 PINN 引擎
# ==============================================================================
class MicroPhysicsNet(nn.Module):
    def __init__(self, input_dim=24):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 128), nn.ReLU(), nn.Linear(128, 64))
        self.classifier = nn.Linear(64, 3)
    def forward(self, x):
        h = self.net(x)
        return h, self.classifier(h)

class MacroQimenNet(nn.Module):
    def __init__(self, input_dim=12):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 64), nn.Tanh(), nn.Linear(64, 64))
        self.classifier = nn.Linear(64, 3)
    def forward(self, x):
        h = self.net(x)
        return h, self.classifier(h)

class DialecticalSynthesizer(nn.Module):
    def __init__(self):
        super().__init__()
        self.micro_net = MicroPhysicsNet(input_dim=24)
        self.macro_net = MacroQimenNet(input_dim=12)
        self.attention_gate = nn.Sequential(
            nn.Linear(64 + 64, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
            nn.Softmax(dim=1)
        )
        self.final_classifier = nn.Linear(64, 3)

    def forward(self, x):
        x_micro, x_macro = x[:, :24], x[:, 24:]
        h_micro, p_micro = self.micro_net(x_micro)
        h_macro, p_macro = self.macro_net(x_macro)
        
        combined_h = torch.cat([h_micro, h_macro], dim=1)
        attn_weights = self.attention_gate(combined_h)
        w_micro, w_macro = attn_weights[:, 0:1], attn_weights[:, 1:2]
        
        h_syn = w_micro * h_micro + w_macro * h_macro
        final_pred = self.final_classifier(h_syn)
        return final_pred, h_micro, h_macro, p_micro, p_macro, w_macro

class PINNPhysicsEngine:
    def __init__(self):
        self.res_net = nn.Sequential(nn.Linear(36, 16), nn.Tanh(), nn.Linear(16, 2), nn.Hardtanh(-0.15, 0.15))

    def evaluate_physics(self, t: UnifiedMarineTelemetry, norm_vec: np.ndarray) -> dict:
        kd_base = 1.00 if t.tp_s > 12.0 else 0.883
        kw_base = 1.00 if t.delta_theta_deg >= 45.0 else 0.78
        with torch.no_grad():
            res = self.res_net(torch.FloatTensor(norm_vec).unsqueeze(0)).squeeze(0).numpy()
        kd, kw = float(np.clip(kd_base + res[0], 0.1, 1.2)), float(np.clip(kw_base + res[1], 0.1, 1.2))
        hs_pier = round(t.hs_cwa * kd, 2)
        w_local = round(t.w_cwa * kw, 2)
        ukc = round((t.namr_multibeam_depth_m + t.tide_eta_m) - (t.d_draft + t.s_quat) - (hs_pier * 0.5), 2)
        fb_pier = round(3.20 - t.tide_eta_m, 2)
        has_veto = (hs_pier > 1.20 or w_local > 10.80 or ukc < 1.50 or fb_pier < 0.50)
        return {"hs_pier_m": hs_pier, "w_local_ms": w_local, "ukc_m": ukc, "fb_pier_m": fb_pier, "has_veto": has_veto}

# ==============================================================================
# 3. 系統中樞與相對精確度引擎
# ==============================================================================
class AutonomousDialecticalOrchestrator:
    def __init__(self, model_path="model_v36D.11.0.pt"):
        self.extractor = GEM36DNormalizedFeatureExtractor()
        self.pinn_engine = PINNPhysicsEngine()
        self.policy = DialecticalSynthesizer()
        self.optimizer = optim.Adam(self.policy.parameters(), lr=0.001)
        self.model_path = model_path
        if os.path.exists(self.model_path):
            self.policy.load_state_dict(torch.load(self.model_path, map_location="cpu", weights_only=True))
            print(f"✅ 載入辯證大腦權重: {self.model_path}")

class PrecisionConvergenceEngine(nn.Module):
    """相對精確度雙核收斂優化器 (v36D.11.0)"""
    def __init__(self, orchestrator: AutonomousDialecticalOrchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.variance_estimator = nn.Sequential(
            nn.Linear(36, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
            nn.Softplus()
        )

    def forward(self, telemetry: UnifiedMarineTelemetry):
        norm_vec = self.orchestrator.extractor.build_normalized_vector(telemetry)
        x_tensor = torch.FloatTensor(norm_vec).unsqueeze(0)
        
        final_pred, _, _, _, _, w_macro = self.orchestrator.policy(x_tensor)
        sigmas = self.variance_estimator(x_tensor)
        sigma_micro, sigma_macro = sigmas[:, 0:1], sigmas[:, 1:2]
        
        precision_micro = 1.0 / (sigma_micro + 1e-6)
        precision_macro = 1.0 / (sigma_macro + 1e-6)
        converged_precision = precision_micro + precision_macro
        converged_sigma = 1.0 / (converged_precision + 1e-6)
        
        pinn_metrics = self.orchestrator.pinn_engine.evaluate_physics(telemetry, norm_vec)
        action_idx = int(torch.argmax(final_pred, dim=1).item())
        res_map = {0: "🟢 放行", 1: "🟡 限制靠泊", 2: "🔴 封島/防颱"}
        
        return {
            "decision": res_map[action_idx],
            "converged_uncertainty_sigma": round(float(converged_sigma.item()), 4),
            "precision_gain_pct": round(float((precision_micro / converged_precision).item()) * 100, 2),
            "physics_veto": pinn_metrics["has_veto"],
            "confidence_score": round(float(torch.max(F.softmax(final_pred, dim=1)).item()) * 100, 2),
            "w_macro": float(w_macro.item())
        }
