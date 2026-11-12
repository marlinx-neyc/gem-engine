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
        else:
            return {"id": "OFF", "name": "離峰巡查籌備期", "target_time": "離峰", "is_window": False}

    def arbitrate_consensus(
        self,
        announcement: dict,
        vessel_res: dict,
        physics_res: dict,
        cctv_res: dict,
        dt: datetime = None
    ) -> Dict[str, Any]:
        win = self.get_official_window(dt)
        wufu = vessel_res.get("official_wufu", {})
        nlp_veto = (announcement.get("official_veto", 0) == 1)
        vessel_docked = bool(wufu.get("is_docked_island", False))
        phys_veto = bool(physics_res.get("hard_veto", False))
        dock_desc = wufu.get("dock_desc", "公務船位置待同步")
        m = physics_res.get("metrics", {})

        if nlp_veto and not vessel_docked and phys_veto:
            consensus_status = "🔴【多重驗證一致·封島】官方公告封島 ｜ 五福號未靠泊 ｜ GEM 物理熔斷 (VETO)"
            trust_score = "100.0% (三重吻合)"
            final_action = "🔴 全線剛性熔斷（禁止靠泊）"
        elif not nlp_veto and vessel_docked and not phys_veto:
            consensus_status = "🟢【多重驗證一致·開放】官方開放營運 ｜ 五福號確認靠泊 ｜ 水動力安全合規"
            trust_score = "100.0% (三重吻合)"
            final_action = physics_res["action_mode"]
        elif nlp_veto and vessel_docked and not phys_veto:
            consensus_status = f"🟡【字庫延遲校正·放行】官網字庫留存過期封島詞，但五福號於「{win['name']}」已實體驗證靠島且水動力合規，裁定現場放行！"
            trust_score = "94.5% (現場實船優先)"
            final_action = "🟡 現場放行 (公務船已靠島)"
        elif not nlp_veto and (not vessel_docked and phys_veto):
            consensus_status = f"🔴【突發海況預警·熔斷】官方文字尚未標註封島，但水動力漫頂超標 (Hs={m.get('hs')}m)，GEM 啟動剛性熔斷！"
            trust_score = "98.2% (物理安全防線優先)"
            final_action = "🔴 突發剛性熔斷（禁止靠泊）"
        else:
            consensus_status = f"🟡【多源動態校核】時段: {win['name']} ｜ 實時浪高 Hs={m.get('hs')}m / 週期 Tp={m.get('tp')}s ｜ GEM 物理計算裁定"
            trust_score = "92.5% (實時海氣象融合)"
            final_action = physics_res["action_mode"]

        return {
            "current_window": win,
            "consensus_status": consensus_status,
            "trust_score": trust_score,
            "final_action": final_action,
            "vessel_docked": vessel_docked,
            "dock_desc": dock_desc
        }
