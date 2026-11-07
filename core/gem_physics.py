import numpy as np

class GemPhysicsEngine:
    def __init__(self):
        self.d_chart_north = 8.50
        self.d_chart_south = 9.80
        self.d_draft = 1.20

    def evaluate_physics(self, telemetry: dict, cctv_res: dict, bias_offset: float = 0.0) -> dict:
        hs, tp, w = telemetry["hs"], telemetry["tp"], telemetry["w"]
        delta_theta, tide = telemetry["monsoon_angle"], telemetry["tide"]

        kd = 1.00 if tp >= 12.0 else (0.62 if delta_theta < 45.0 else 1.00)
        hs_pier = float(hs * kd)
        kw = 0.78 if delta_theta < 35.0 else (0.88 if delta_theta < 45.0 else 1.00)
        weff = float(w * abs(np.cos(np.radians(delta_theta))) * kw)

        ukc_south = float((self.d_chart_south + tide) - self.d_draft - hs_pier)
        ukc_north = float((self.d_chart_north + tide) - self.d_draft - hs_pier)
        fb_override = cctv_res.get("fb_pier_override", 2.40)

        hard_veto = bool(hs_pier > 1.13 or weff > 10.17 or ukc_north < 1.50 or fb_override < 0.50)

        return {
            "hard_veto": hard_veto,
            "p_veto": 0.999 if hard_veto else 0.02,
            "metrics": {
                "hs_pier": round(hs_pier, 2),
                "weff": round(weff, 2),
                "ukc": round(ukc_north, 2),
                "ukc_south": round(ukc_south, 2),
                "fb": round(fb_override, 2)
            }
        }
