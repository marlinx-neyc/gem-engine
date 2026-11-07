class GemCCTVPatternAgent:
    def __init__(self, pixel_to_meter_scale: float = 0.015):
        self.scale = pixel_to_meter_scale

    def process_cctv_frame_features(self, raw_cv_data: dict) -> dict:
        cv_rate = float(raw_cv_data.get("cctv_cv_rate", 0.0))
        t_overtop_pct = cv_rate * 12.5
        fb_pier = 0.15 if t_overtop_pct >= 15.0 else 2.40
        return {
            "cctv_cv_rate": cv_rate,
            "t_overtop_pct": round(t_overtop_pct, 1),
            "fb_pier_override": fb_pier,
            "is_overtopping": t_overtop_pct >= 15.0
        }
