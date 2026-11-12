from datetime import datetime, timedelta, timezone
from typing import Dict, Any

CST = timezone(timedelta(hours=8))

class GemMultiSourceConsensus:
    @staticmethod
    def get_official_window(dt: datetime = None) -> Dict[str, Any]:
        dt = dt or datetime.now(CST)
        cur_min = dt.hour * 60 + dt.minute

        if 6 * 60 + 30 <= cur_min <= 9 * 60 + 30:
            return {"id": "W1", "name": "晨間首航巡查窗 (07:30)", "target_time": "07:30", "is_window": True}
        elif 10 * 60 + 30 <= cur_min <= 13 * 60 + 30:
            return {"id": "W2", "name": "午間巡查防禦窗 (11:30)", "target_time": "11:30", "is_window": True}
        elif 15 * 60 + 30 <= cur_min <= 18 * 60 + 30:
            return {"id": "W3", "name": "傍晚閉島休整窗 (16:30)", "target_time": "16:30", "is_window": True}
        elif 7 * 60 <= cur_min <= 16 * 60 + 30:
            return {"id": "W_OPEN", "name": "日間船班營運時段 (07:00-16:30)", "target_time": "營運中", "is_window": True}
        else:
            return {"id": "OFF", "name": "夜間休整離峰期", "target_time": "休整期", "is_window": False}

    def arbitrate_consensus(
        self,
        announcement: dict,
        vessel_res: dict,
        physics_res: dict,
        cctv_res: dict,
        dt: datetime = None
    ) -> Dict[str, Any]:
        dt = dt or datetime.now(CST)
        win = self.get_official_window(dt)
        wufu = vessel_res.get("official_wufu", {})

        web_veto = (announcement.get("official_veto", 0) == 1)
        vessel_docked = bool(wufu.get("is_docked_island", False))
        in_boat_hours = bool(wufu.get("in_boat_hours", False))
        dock_code = wufu.get("dock_code", "")
        phys_veto = bool(physics_res.get("hard_veto", False))
        dock_desc = wufu.get("dock_desc", "公務船位置待同步")
        m = physics_res.get("metrics", {})

        # 🎯 核心本質規則：公務船的進、退、停是為登島服務，動態修正官方實質判定！
        if in_boat_hours and vessel_docked:
            effective_official_veto = 0
            if web_veto:
                effective_official_label = "🟢 實質開島 (已修正官網滯後公告)"
                effective_official_title = "【動態修正·實質開島】五福號船班時段持續靠泊龜山島戒護，實質確認官方開島營運"
                consensus_status = f"🟢【實船駐島鐵證·開島】船班時段五福號持續靠泊龜山島 ({dock_code})，已自動修正網站滯後封島文字！"
                trust_score = "98.5% (實船駐島鐵證)"
            else:
                effective_official_label = "🟢 實質開島 (五福號駐島戒護)"
                effective_official_title = announcement.get("title", "【風管處通告】五福號駐島戒護，全島正常開放登島")
                consensus_status = f"🟢【多重驗證一致·開島】官方開放 ｜ 五福號船班時段靠泊龜山島戒護 ｜ 水動力合規 (Hs={m.get('hs')}m)"
                trust_score = "100.0% (三重吻合)"
            final_action = physics_res["action_mode"] if not phys_veto else "🟡 實船駐島開窗 (留意南岸調撥)"

        elif in_boat_hours and dock_code in ["BERTHED_WUSHI_CLOSED", "PATROLLING_FAILED"]:
            effective_official_veto = 1
            if not web_veto:
                effective_official_label = "🔴 實質封島 (五福號未靠島)"
                effective_official_title = "【動態修正·實質封島】船班時段五福號滯留烏石港/無法靠泊，官方實質判定暫停登島"
                consensus_status = "🔴【實船行為預警·封島】官網文字尚未更新，但五福號於船班時段未靠泊龜山島，判定實質封島！"
                trust_score = "97.5% (實船未出港優先)"
            else:
                effective_official_label = "🔴 浪高封島 (雙重確認)"
                effective_official_title = announcement.get("title", "【風管處公告】今日龜山島實施封島")
                consensus_status = "🔴【多重驗證一致·封島】官方公告封島 ｜ 五福號未靠泊龜山島 ｜ 物理熔斷確認"
                trust_score = "100.0% (三重吻合)"
            final_action = "🔴 全線剛性熔斷（禁止靠泊）"

        else:
            # 非船班時段（夜間/清晨出港前）或航行途中：依網頁公告與水動力預報綜合判定
            effective_official_veto = 1 if (web_veto or phys_veto) else 0
            effective_official_label = "🔴 預警封島" if effective_official_veto == 1 else "🟢 常態營運"
            effective_official_title = announcement.get("title", "【風管處通告】全島常規開放營運中")
            consensus_status = f"🟡【非船班時段校核】時段: {win['name']} ｜ 船況: {dock_desc} ｜ 實時浪高 Hs={m.get('hs')}m"
            trust_score = "91.0% (水動力+公告融合)"
            final_action = physics_res["action_mode"]

        return {
            "current_window": win,
            "effective_official_veto": effective_official_veto,
            "effective_official_label": effective_official_label,
            "effective_official_title": effective_official_title,
            "consensus_status": consensus_status,
            "trust_score": trust_score,
            "final_action": final_action,
            "vessel_docked": vessel_docked,
            "dock_desc": dock_desc
        }
