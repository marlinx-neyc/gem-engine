class GemCCTVPatternAgent:
    def process_cctv_frame_features(self, raw_cv_data: dict) -> dict:
        cv_rate = float(raw_cv_data.get("cctv_cv_rate", 0.0))
        t_overtop_pct = round(min(100.0, cv_rate * 12.5), 1)
        fb_north_override = 0.15 if t_overtop_pct >= 18.0 else (0.55 if t_overtop_pct >= 8.0 else 2.40)
        fb_south_override = 0.85 if t_overtop_pct >= 18.0 else 2.80
        is_overtopping = t_overtop_pct >= 18.0
        return {
            "cctv_cv_rate": cv_rate,
            "t_overtop_pct": t_overtop_pct,
            "fb_north_override": fb_north_override,
            "fb_south_override": fb_south_override,
            "is_overtopping": is_overtopping,
            "north_cam_status": f"🔴 越浪警戒 ({t_overtop_pct}%)" if is_overtopping else f"🟢 LIVE 25FPS (漫頂率 {t_overtop_pct}%)",
            "south_cam_status": f"🟡 湧浪監控 (FB {fb_south_override}m)" if is_overtopping else f"🟢 LIVE 25FPS (FB {fb_south_override}m)",
            "visual_eye_status": "🔴 CCTV 視覺偵測北岸碼頭漫頂 (禁止北岸靠泊)" if is_overtopping else "🟢 CCTV 畫面顯示碼頭水深乾舷合規"
        }
