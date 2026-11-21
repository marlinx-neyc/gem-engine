import math
import numpy as np

class GemPhysicsEngine:
    def __init__(self):
        self.d_chart_north = 8.50
        self.d_chart_south = 9.80
        self.d_draft = 1.20
        self.c_b = 0.65

    @staticmethod
    def compute_squat(v_speed_kts: float, d_chart: float, d_draft: float = 1.20, c_b: float = 0.65) -> float:
        g = 9.80665
        v_ms = v_speed_kts * 0.514444
        fh = min(0.95, v_ms / math.sqrt(g * max(0.5, d_chart)))
        squat = (c_b * (v_speed_kts ** 2)) / (30.0 * (d_chart / d_draft)) * (1.0 / math.sqrt(max(0.05, 1.0 - fh ** 2))) * 0.50
        return round(squat, 2)

    def evaluate_physics(self, telemetry: dict, cctv_res: dict) -> dict:
        if telemetry.get("tsunami_pulse_alert"):
            return {"hard_veto": True, "is_tier0": True, "tier0_reason": "[Tier-0] 海嘯預警！", "action_id": 0, "p_veto": 1.0,
                    "action_mode": "🔴 0.0% 物理 VETO 熔斷（海嘯預警）", "badge": "🔴 Tier-0 海嘯熔斷", "metrics": {}}
        if float(telemetry.get("local_pga_gal", 0.0)) >= 250.0:
            return {"hard_veto": True, "is_tier0": True, "tier0_reason": "[Tier-0] 強震警告！", "action_id": 0, "p_veto": 1.0,
                    "action_mode": "🔴 0.0% 物理 VETO 熔斷（強震警報）", "badge": "🔴 Tier-0 強震熔斷", "metrics": {}}
        if float(telemetry.get("visibility_m", 5000.0)) < 500.0:
            return {"hard_veto": True, "is_tier0": True, "tier0_reason": "[Tier-0] 濃霧致盲！", "action_id": 0, "p_veto": 1.0,
                    "action_mode": "🔴 0.0% 物理 VETO 熔斷（濃霧致盲）", "badge": "🔴 Tier-0 濃霧熔斷", "metrics": {}}

        hs = float(telemetry["hs"])
        tp = float(telemetry["tp"])
        w = float(telemetry["w"])
        delta_theta = float(telemetry["monsoon_angle"])
        tide = float(telemetry["tide"])
        v_speed_kts = float(telemetry.get("v_speed_kts", 12.5))
        cv_rate = float(cctv_res.get("cctv_cv_rate", telemetry.get("cctv_cv_rate", 0.0)))
        passenger_count = int(telemetry.get("passenger_count", 150))
        high_tide_hour = float(telemetry.get("high_tide_hour", 10.0))
        alpha_tune = float(telemetry.get("alpha_tune", 0.85))

        kd_north = 1.00 if tp >= 12.0 else 0.883
        kd_south = 1.00 if tp >= 12.0 else 0.72
        hs_pier_north = round(hs * kd_north, 2)
        hs_pier_south = round(hs * kd_south, 2)

        kw = 0.78 if delta_theta < 35.0 else (0.88 if delta_theta < 45.0 else 1.00)
        weff = round(w * abs(math.cos(math.radians(delta_theta))) * kw, 2)

        squat_north = self.compute_squat(v_speed_kts, self.d_chart_north, self.d_draft, self.c_b)
        squat_south_3kt = self.compute_squat(3.0, self.d_chart_south, self.d_draft, self.c_b)
        ukc_north = round((self.d_chart_north + tide) - (self.d_draft + squat_north) - hs_pier_north, 2)
        ukc_south = round((self.d_chart_south + tide) - (self.d_draft + squat_south_3kt) - hs_pier_south, 2)

        fb_north = float(cctv_res.get("fb_north_override", 0.15 if cv_rate > 0.0 else round(3.20 - tide, 2)))
        fb_south = float(cctv_res.get("fb_south_override", 0.15 if cv_rate > 0.0 else round(3.20 - tide, 2)))

        hard_veto = bool(
            (hs_pier_north > 1.13 and hs_pier_south > 1.13)
            or weff > 10.17
            or (ukc_north < 1.50 and ukc_south < 1.50)
            or (fb_north < 0.50 and fb_south < 0.50)
        )

        active_hs = hs_pier_north if hs_pier_north <= 1.13 else hs_pier_south
        active_ukc = ukc_north if hs_pier_north <= 1.13 else ukc_south
        active_fb = fb_north if hs_pier_north <= 1.13 else fb_south
        active_squat = squat_north if hs_pier_north <= 1.13 else squat_south_3kt

        k_flux = round(active_hs + (weff * 0.1) + active_squat, 4)
        v_impedance = round(max(0.05, 0.5 * active_ukc + 0.5 * active_fb), 4)
        e_net = round(k_flux / v_impedance, 4)
        p_veto = round(1.0 / (1.0 + math.exp(-(e_net - 1.00) / (0.25 * alpha_tune))), 4)

        if hard_veto or p_veto > 0.80:
            if cv_rate > 1.0 and hs_pier_south <= 1.13 and weff <= 10.17 and ukc_south >= 1.50:
                action_id = 3
                action_mode = "⏱️ Q3 動態開窗 (11:20 剛性止登 / 14:20 強制清島)"
                badge = "⏱️ Q3 動態開窗"
            else:
                action_id = 0
                action_mode = "🔴 0.0% 物理 VETO 熔斷（禁止靠泊）"
                badge = "🔴 0.0% 物理 VETO 熔斷"
        elif (0.20 <= p_veto <= 0.80) or (tide < 0.40) or (35.0 <= delta_theta < 45.0) or (hs_pier_north > 1.13 and hs_pier_south <= 1.13):
            action_id = 1
            action_mode = "🟡 Q2 游擊調撥 (移防南岸靠泊 / 限速 <= 3.0 kts)"
            badge = "🟡 Q2 游擊調撥"
        else:
            action_id = 2
            action_mode = "🟢 100.0% Q1 全線開放 (靠泊北岸主泊位)"
            badge = "🟢 100.0% Q1 全線開放"

        evac_minutes = int(math.ceil(passenger_count / 10.0 + max(0.0, (active_squat - 0.50) * 15.0) + 5.0))
        peak_h = (high_tide_hour + 3.5) % 24.0
        milk_sea_peak = f"{int(peak_h):02d}:{int((peak_h % 1) * 60):02d}"

        return {
            "hard_veto": hard_veto,
            "is_tier0": False,
            "tier0_reason": "",
            "action_id": action_id,
            "p_veto": p_veto,
            "action_mode": action_mode,
            "badge": badge,
            "metrics": {
                "hs": round(hs, 2), "tp": round(tp, 1),
                "pressure": round(telemetry.get("pressure", 1013.0), 1),
                "pressure_3h": round(telemetry.get("pressure_3h", 0.0), 1),
                "hs_pier_north": hs_pier_north, "hs_pier_south": hs_pier_south,
                "kd_north": kd_north, "kd_south": kd_south,
                "w": round(w, 2), "weff": weff, "kw": kw, "delta_theta": round(delta_theta, 1),
                "tide": round(tide, 2),
                "squat_north": squat_north, "squat_south_3kt": squat_south_3kt,
                "ukc_north": ukc_north, "ukc_south": ukc_south,
                "fb_north": fb_north, "fb_south": fb_south,
                "cv_rate": cv_rate,
                "k_flux": k_flux, "v_impedance": v_impedance,
                "e_net": e_net, "p_veto": p_veto,
                "evac_minutes": evac_minutes, "milk_sea_peak": milk_sea_peak
            }
        }
