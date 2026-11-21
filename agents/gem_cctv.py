class GemCCTVPatternAgent:
    def process_cctv_frame_features(self, telemetry: dict) -> dict:
        tide = float(telemetry.get("tide", 0.5))
        if "cctv_cv_rate" in telemetry and telemetry["cctv_cv_rate"] is not None:
            cv_rate = float(telemetry["cctv_cv_rate"])
        else:
            hs = float(telemetry.get("hs", 0.8))
            cv_rate = round(max(0.0, (tide - 1.30) * 8.0 + max(0.0, hs - 1.10) * 2.5), 2)

        res = {
            "cctv_cv_rate": round(cv_rate, 2),
            "vision_status": "OVERTOPPING_DETECTED" if cv_rate > 0.0 else "CLEAR_PIER"
        }
        if cv_rate > 0.0:
            res["fb_north_override"] = 0.15
            res["fb_south_override"] = 0.15
        return res
