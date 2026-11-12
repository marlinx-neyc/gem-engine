from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

class GemSignalAgent:
    def __init__(self):
        self._last_marquee_cache = None

    def purge_internal_cache(self):
        self._last_marquee_cache = None

    def package_live_status(
        self,
        physics_res: dict,
        consensus_res: dict,
        announcement: dict,
        vessel_res: dict,
        swell_res: dict = None,
        cctv_res: dict = None,
        telemetry: dict = None
    ) -> dict:
        self.purge_internal_cache()
        telemetry = telemetry or {}
        now_str = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")
        off_v = vessel_res.get("official_wufu", {})
        win = consensus_res["current_window"]
        m = physics_res.get("metrics", {})

        official_title = consensus_res.get("effective_official_title") or announcement.get("title", "【風管處通告】全島常規開放營運中")
        official_label = consensus_res.get("effective_official_label", "🟢 常態營運")
        vessel_msg = consensus_res.get("dock_desc", "公務船動態校核中")
        final_action = consensus_res.get("final_action", "🟡 機動觀望")

        marquee_str = (
            f"📢 官方實質判定：{official_title} ｜ "
            f"🚢 公務船 ({win['target_time']})：{vessel_msg} ｜ "
            f"🤖 GEM 仲裁：{final_action} (Hs:{m.get('hs')}m, 南/北折算:{m.get('hs_pier_south')}/{m.get('hs_pier_north')}m, 風速:{m.get('w')}m/s) ｜ "
            f"⏱️ 校核：{now_str}"
        )

        self._last_marquee_cache = marquee_str

        return {
            "updated_at": now_str,
            "decision": final_action,
            "consensus_status": consensus_res["consensus_status"],
            "trust_score": consensus_res["trust_score"],
            "p_veto": physics_res["p_veto"],
            "official_veto": consensus_res.get("effective_official_veto", 0),
            "tomorrow_veto": announcement.get("tomorrow_veto", 0),
            "effective_official_label": official_label,
            "official_title": official_title,
            "official_body": announcement.get("body", ""),
            "official_wufu_position": off_v.get("coord_str", "24.84375° N, 121.94378° E"),
            "official_wufu_status": vessel_msg,
            "official_wufu_dist_wushi": f"{off_v.get('dist_wushi_m', 10700.0) / 1000.0:.1f} km",
            "official_wufu_dist_piers": f"{off_v.get('dist_north_m', 5.0)}m / {off_v.get('dist_south_m', 540.0)}m",
            "current_window_name": win["name"],
            "wushi_port_flux_ships_hr": vessel_res.get("wushi_port_fleet_flux", {}).get("v_flux_ships_per_hour", 42.0),
            "cctv_status": cctv_res or {},
            "typhoon_info": telemetry.get("typhoon_info", {}),
            "daily_forecast": telemetry.get("daily_forecast", []),
            "swell_forecast": swell_res or {},
            "metrics": m,
            "marquee_msg": marquee_str
        }
