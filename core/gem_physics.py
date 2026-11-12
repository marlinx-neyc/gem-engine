import numpy as np

class GemPhysicsEngine:
    def __init__(self):
        self.d_chart_north = 8.50
        self.d_chart_south = 9.80
        self.d_draft = 1.20

    def evaluate_physics(self, telemetry: dict, cctv_res: dict) -> dict:
        hs, tp, w = telemetry["hs"], telemetry["tp"], telemetry["w"]
        delta_theta, tide = telemetry["monsoon_angle"], telemetry["tide"]

        kd_north = 1.00 if tp >= 12.0 else (0.75 if delta_theta < 45.0 else 1.00)
        kd_south = 0.55
        hs_pier_north = float(hs * kd_north)
        hs_pier_south = float(hs * kd_south)

        kw = 0.78 if delta_theta < 35.0 else (0.88 if delta_theta < 45.0 else 1.00)
        weff = float(w * abs(np.cos(np.radians(delta_theta))) * kw)

        ukc_south = float((self.d_chart_south + tide) - self.d_draft - hs_pier_south)
        ukc_north = float((self.d_chart_north + tide) - self.d_draft - hs_pier_north)

        fb_north = cctv_res.get("fb_north_override", 2.40)
        fb_south = cctv_res.get("fb_south_override", 2.80)

        hard_veto = bool(hs_pier_north > 1.80 or weff > 10.17 or ukc_north < 1.00 or fb_north < 0.20)

        action_mode = "🔴 全線剛性熔斷（禁止靠泊）"
        badge = "🔴 0.0% 物理 VETO 熔斷"

        if not hard_veto:
            if fb_north >= 0.50 and ukc_north >= 1.50 and hs_pier_north <= 0.95:
                action_mode = "🟢 常態開放靠泊 (北岸 Q1)"
                badge = "🟢 100.0% 常規開放"
            elif fb_south >= 0.50 and ukc_south >= 1.50:
                action_mode = "🟡 戰術機動調撥 (移防南岸靠泊 Q2)"
                badge = "🟡 80.0% 移防南岸"
            elif 0.30 <= fb_north < 0.50:
                action_mode = "🟡 晨間延滯觀望 (建議延後至 08:30 評估)"
                badge = "🟡 50.0% 延滯開窗"
            else:
                action_mode = "⚠️ 防禦性早退撤離 (午後潮位加成警報)"
                badge = "⚠️ 防禦性早退"

        return {
            "hard_veto": hard_veto,
            "p_veto": 0.999 if hard_veto else 0.05,
            "action_mode": action_mode,
            "badge": badge,
            "metrics": {
                "hs": round(hs, 2),
                "tp": round(tp, 1),
                "pressure": round(telemetry.get("pressure", 1013.0), 1),
                "pressure_3h": round(telemetry.get("pressure_3h", 0.0), 1),
                "hs_pier_north": round(hs_pier_north, 2),
                "hs_pier_south": round(hs_pier_south, 2),
                "w": round(w, 2),
                "weff": round(weff, 2),
                "delta_theta": round(delta_theta, 1),
                "ukc_north": round(ukc_north, 2),
                "ukc_south": round(ukc_south, 2),
                "fb_north": round(fb_north, 2),
                "fb_south": round(fb_south, 2)
            }
        }
