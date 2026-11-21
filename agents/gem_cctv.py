class GemCCTVPatternAgent:
    def process_cctv_frame_features(self, raw_cv_data: dict) -> dict:
        cv_rate = float(raw_cv_data.get("cctv_cv_rate", 0.0))
        tide = float(raw_cv_data.get("tide", 0.95))
        t_overtop_pct = round(min(100.0, cv_rate * 12.5), 1)
        base_fb = round(3.20 - tide, 2)
        # V66.5 第 2.3 節與第 3 節：一旦檢測到 CV > 0.0 p/min，強制覆寫 FB = 0.15m
        fb_north_override = 0.15 if cv_rate > 0.0 else base_fb
        fb_south_override = 0.15 if cv_rate > 0.0 else base_fb
        is_overtopping = (cv_rate > 0.0)
        return {
            "cctv_cv_rate": cv_rate,
            "t_overtop_pct": t_overtop_pct,
            "fb_north_override": fb_north_override,
            "fb_south_override": fb_south_override,
            "is_overtopping": is_overtopping,
            "north_cam_status": f"🔴 越浪覆寫 FB=0.15m ({cv_rate} p/min)" if is_overtopping else f"🟢 LIVE 30FPS (FB {fb_north_override}m)",
            "south_cam_status": f"🔴 越浪覆寫 FB=0.15m ({cv_rate} p/min)" if is_overtopping else f"🟢 LIVE 30FPS (FB {fb_south_override}m)",
            "visual_eye_status": "🔴 Vision-PINN 偵測引橋越浪 (CV>0 強制乾舷壓制 0.15m)" if is_overtopping else "🟢 Vision-PINN 畫面顯示碼頭乾舷合規"
        }
