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

    def _check_active_manual_override(self, existing_state: dict, dt: datetime) -> dict:
        if not existing_state:
            return {"active": False}
        ov = existing_state.get("manual_override", {})
        if not ov.get("active"):
            return {"active": False}
        exp_str = ov.get("expires_at", "")
        if exp_str:
            try:
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=CST)
                if dt >= exp_dt:
                    return {"active": False}
            except Exception:
                pass
        return ov

    def arbitrate_consensus(
        self,
        announcement: dict,
        vessel_res: dict,
        physics_res: dict,
        cctv_res: dict,
        existing_state: dict = None,
        dt: datetime = None
    ) -> Dict[str, Any]:
        dt = dt or datetime.now(CST)
        win = self.get_official_window(dt)
        wufu = vessel_res.get("official_wufu", {})

        web_veto = (announcement.get("official_veto", 0) == 1)
        ann_scope = announcement.get("scope", "FULL_DAY")
        vessel_docked = bool(wufu.get("is_docked_island", False))
        in_boat_hours = bool(wufu.get("in_boat_hours", False))
        dock_code = wufu.get("dock_code", "")
        vector_state = wufu.get("vector_state", "INITIAL_POINT")
        phys_veto = bool(physics_res.get("hard_veto", False))
        dock_desc = wufu.get("dock_desc", "公務船位置待同步")
        vector_desc = wufu.get("vector_desc", "軌跡校核中")
        m = physics_res.get("metrics", {})

        # 🛡️ Priority 0: 人工緊急覆寫鎖 (防止定時排程覆蓋現場 LINE 臨時封島)
        active_ov = self._check_active_manual_override(existing_state, dt)
        if active_ov.get("active"):
            ov_reason = active_ov.get("reason", "值班指揮官啟動人工緊急覆寫鎖")
            ov_scope = active_ov.get("scope", "FULL_DAY")
            ov_action = int(active_ov.get("action", 0))
            is_ov_veto = (ov_action == 0)
            scope_tag = "下午封島半天 (12:00-17:30)" if ov_scope == "AFTERNOON" else "全日封島管制"
            return {
                "current_window": win,
                "manual_override": active_ov,
                "web_official_veto": 1 if is_ov_veto else 0,
                "announcement_scope": ov_scope,
                "effective_official_veto": 1 if is_ov_veto else 0,
                "effective_official_label": f"🔴 現場覆寫·{scope_tag}" if is_ov_veto else "🟢 現場覆寫開島",
                "effective_official_title": f"【現場群組緊急通告】{ov_reason}",
                "consensus_status": f"🔒【人工覆寫鎖生效中】{ov_reason} (鎖定至 {active_ov.get('expires_at', '17:30 CST')})",
                "trust_score": "100.0% (指揮官人工覆寫鎖)",
                "final_action": f"🔴 全線剛性熔斷（{scope_tag}）" if is_ov_veto else "🟢 現場放行（覆寫解鎖）",
                "vessel_docked": vessel_docked,
                "dock_desc": dock_desc,
                "vector_desc": vector_desc,
                "four_way_summary": {
                    "pos": dock_desc,
                    "traj": vector_desc,
                    "phys": physics_res["badge"],
                    "off": f"🔒 {scope_tag}"
                }
            }

        # 🎯 Priority 1: 盤中路徑顯示返航烏石港或試靠失敗 -> 最高優先級判定臨時封島
        if in_boat_hours and vector_state in ["RETREATING_TO_WUSHI", "LOITERING_FAILED_DOCK"]:
            effective_official_veto = 1
            effective_official_label = "🔴 實質封島 (路徑確認撤離)"
            effective_official_title = "【四維仲裁·臨時封島】五福號軌跡顯示返航烏石港/試靠失敗，現場執行封島疏散"
            consensus_status = f"🔴【四維路徑鐵證·封島】{vector_desc} ｜ 官網文字未更新前提前觸發熔斷！"
            trust_score = "99.2% (路徑向量實證)"
            final_action = "🔴 全線剛性熔斷（路徑確認撤離）"

        # 🎯 Priority 2: 船班時段五福號穩定靠泊碼頭 -> 修正官網滯後公告，判定實質開島
        elif in_boat_hours and vessel_docked:
            effective_official_veto = 0
            if web_veto:
                effective_official_label = "🟢 實質開島 (已修正官網滯後)"
                effective_official_title = "【動態修正·實質開島】五福號船班時段持續靠泊龜山島戒護，實質確認官方開島營運"
                consensus_status = f"🟢【實船駐島鐵證·開島】五福號持續靠泊龜山島 ({dock_code})，已自動修正網站滯後封島文字！"
                trust_score = "98.5% (實船駐島鐵證)"
            else:
                effective_official_label = "🟢 實質開島 (五福號駐島戒護)"
                effective_official_title = announcement.get("title", "【風管處通告】五福號駐島戒護，全島正常開放登島")
                consensus_status = f"🟢【四維驗證一致·開島】官網開放 ｜ 五福號駐泊戒護 ｜ 物理合規 (Hs={m.get('hs')}m)"
                trust_score = "100.0% (四維吻合)"
            final_action = physics_res["action_mode"] if not phys_veto else "🟡 實船駐島開窗 (留意南岸調撥)"

        # 🎯 Priority 3: 船班時段滯留烏石港未出港 -> 實質封島
        elif in_boat_hours and dock_code == "BERTHED_WUSHI_CLOSED":
            effective_official_veto = 1
            effective_official_label = "🔴 實質封島 (五福號未出港)"
            effective_official_title = "【動態修正·實質封島】船班時段五福號停泊烏石港未出港，官方實質判定暫停登島"
            consensus_status = "🔴【實船未出港預警·封島】五福號於船班時段滯留烏石港母港，判定實質封島！"
            trust_score = "98.0% (實船未出港優先)"
            final_action = "🔴 全線剛性熔斷（禁止靠泊）"

        # 🎯 Priority 4: 官網已明確發布今日封島公告 (含非船班時段結算/預警)
        elif web_veto:
            effective_official_veto = 1
            scope_txt = "下午封島半天" if ann_scope == "AFTERNOON" else "官方公告封島"
            effective_official_label = f"🔴 {scope_txt}"
            effective_official_title = announcement.get("title", "【風管處公告】今日龜山島實施封島")
            consensus_status = f"🔴【官方公告封島】{effective_official_title} ｜ 日期面板 D0 已同步修正為封島！"
            trust_score = "100.0% (官方正式公告)"
            final_action = f"🔴 全線剛性熔斷（{scope_txt}）"

        # 🎯 Priority 5: 物理模型領先預警熔斷 (長浪湧升但官網未發)
        elif phys_veto:
            effective_official_veto = 1
            effective_official_label = "🔴 物理預警熔斷 (待船隻確認)"
            effective_official_title = f"【物理模型預警】港池折算波高超標 (Hs={m.get('hs')}m, Tp={m.get('tp')}s)，預警封島"
            consensus_status = f"🔴【物理領先預警·熔斷】官網尚未發布封島，但水動力越浪超標 (Hs={m.get('hs')}m, Tp={m.get('tp')}s)，GEM 提前啟動熔斷！"
            trust_score = "97.2% (水動力領先預警)"
            final_action = "🔴 物理預警熔斷（禁止靠泊）"

        # 🎯 Priority 6: 常態營運
        else:
            effective_official_veto = 0
            effective_official_label = "🟢 常態營運"
            effective_official_title = announcement.get("title", "【風管處通告】全島常規開放營運中")
            consensus_status = f"🟢【四維綜合校核】時段: {win['name']} ｜ {vector_desc} ｜ 實時浪高 Hs={m.get('hs')}m"
            trust_score = "94.0% (水動力+公告融合)"
            final_action = physics_res["action_mode"]

        return {
            "current_window": win,
            "manual_override": {"active": False},
            "web_official_veto": 1 if web_veto else 0,
            "announcement_scope": ann_scope,
            "effective_official_veto": effective_official_veto,
            "effective_official_label": effective_official_label,
            "effective_official_title": effective_official_title,
            "consensus_status": consensus_status,
            "trust_score": trust_score,
            "final_action": final_action,
            "vessel_docked": vessel_docked,
            "dock_desc": dock_desc,
            "vector_desc": vector_desc,
            "four_way_summary": {
                "pos": dock_desc,
                "traj": vector_desc,
                "phys": physics_res["badge"],
                "off": effective_official_label
            }
        }
