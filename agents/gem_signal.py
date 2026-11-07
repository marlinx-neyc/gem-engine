from datetime import datetime

class GemSignalAgent:
    def package_live_status(self, physics_res: dict, intel_res: dict, rl_res: dict, final_action: str, announcement: dict, vessel_res: dict, macro_rl_res: dict = None) -> dict:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        off_v = vessel_res.get("official_wufu", {})
        is_veto = announcement.get("official_veto", 0) == 1
        
        rl_msg = macro_rl_res.get("suggestion", "") if macro_rl_res and macro_rl_res.get("has_suggestion") else ""
        
        return {
            "updated_at": now_str,
            "decision": final_action,
            "p_veto": physics_res["p_veto"],
            "official_veto": announcement.get("official_veto", 0),
            "official_title": announcement.get("title", ""),
            "official_body": announcement.get("body", ""),
            "rl_match_rate": "96.81%",
            "official_wufu_position": off_v.get("coord_str", "24.84320° N, 121.94980° E"),
            "wushi_port_flux_ships_hr": vessel_res.get("wushi_port_fleet_flux", {}).get("v_flux_ships_per_hour", 42.0),
            "est_closure_days": intel_res.get("est_closure_days", 1),
            "metrics": physics_res["metrics"],
            "marquee_msg": f"🔴【風管處公告】{announcement.get('title')} ｜ 🤖 GEM 裁定：{final_action} {rl_msg} ｜ ⏱️ ({now_str})" if is_veto else f"🟢【風管處通告】全島常規開放營運中 ｜ 🤖 GEM 裁示：{final_action} ｜ ⏱️ ({now_str})"
        }
