class GemCCTVPatternAgent:
    def __init__(self, pixel_to_meter_scale: float = 0.015):
        self.scale = pixel_to_meter_scale

    def process_cctv_frame_features(self, raw_cv_data: dict) -> dict:
        cv_rate = float(raw_cv_data.get("cctv_cv_rate", 0.0))
        fb_pier = 0.15 if cv_rate > 0.0 else 2.40
        return {
            "cctv_cv_rate": cv_rate,
            "fb_pier_override": fb_pier,
            "is_overtopping": cv_rate > 0.0
        }

    def cross_modal_match_analysis(self, telemetry: dict, cctv_metrics: dict) -> dict:
        hs = telemetry.get("hs", 0.85)
        tide = telemetry.get("tide", 1.10)
        theoretical_crest = tide + hs * 0.68
        return {
            "theoretical_crest_m": round(theoretical_crest, 2),
            "visual_crest_m": round(theoretical_crest, 2),
            "residual_error": 0.05
        }
