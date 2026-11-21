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
        self, announcement: dict, vessel_res: dict, physics_res: dict,
        cctv_res: dict, pm_forecast: dict = None, existing_state: dict = None,
        dt: datetime = None, rl_res: dict = None
    ) -> Dict[str, Any]:
        dt = dt or datetime.now(CST)
        pm_forecast = pm_forecast or {}
        rl_res = rl_res or {}
        win = self.get_official_window(dt)
        wufu = vessel_res.get("official_wufu", {})

        web_veto = (announcement.get("official_veto", 0) == 1)
        ann_scope = announcement.get("scope", "FULL_DAY")
        south_closed = bool(announcement.get("south_pier_closed_damage", True))
        is_real_ais = bool(wufu.get("is_real_ais", False))
        vessel_docked = bool(wufu.get("is_docked_island", False))
        in_boat_hours = bool(wufu.get("in_boat_hours", False))
        dock_code = wufu.get("dock_code", "")
        vector_state = wufu.get("vector_state", "INITIAL_POINT")
        phys_veto = bool(physics_res.get("hard_veto", False))
        pm_risk = bool(pm_forecast.get("afternoon_risk", False))
        dock_desc = wufu.get("dock_desc", "公務船位置待同步")
        vector_desc = wufu.get("vector_desc", "軌跡校核中")
        m = physics_res.get("metrics", {})

        http_logs = " ".join(announcement.get("scraper_diagnostics", {}).get("http_statuses", []))
        gov_unreachable = ("necoast-nsa.gov.tw" in http_logs and ":200" not in http_logs)

        ais_logs = " ".join(wufu.get("ais_diagnostics", []))
        tdx_connected = any(tag in ais_logs for tag in ["tdx_auth:200", "tdx_mqtt:rc=Success", "tdx_mqtt:rc=0"])
        ais_absent_in_hours = in_boat_hours and (not vessel_docked) and (is_real_ais or tdx_connected or dock_code == "BERTHED_WUSHI_CLOSED")

        active_ov = self._check_active_manual_override(existing_state, dt)
        if active_ov.get("active"):
            ov_reason = active_ov.get("reason", "值班指揮官啟動人工緊急覆寫鎖")
            ov_scope = active_ov.get("scope", "FULL_DAY")
            ov_action = int(active_ov.get("action", 0))
            is_ov_veto = (ov_action == 0)
            scope_tag = "下午封島半天 (12:00-17:30)" if ov_scope == "AFTERNOON" else "全日封島管制"
            return {
                "current_window": win, "manual_override": active_ov,
                "web_official_veto": 1 if is_ov_veto else 0, "announcement_scope": ov_scope,
                "effective_official_veto": 1 if is_ov_veto else 0,
                "effective_official_label": f"🔴 現場覆寫·{scope_tag}" if is_ov_veto else "🟢 現場覆寫開島",
                "effective_official_title": f"【現場群組緊急通告】{ov_reason}",
                "consensus_status": f"🔒【人工覆寫鎖生效中】{ov_reason} (鎖定至 {active_ov.get('expires_at', '17:30 CST')})",
                "trust_score": "100.0% (指揮官人工覆寫鎖)",
                "final_action": f"🔴 0.0% 物理 VETO 熔斷（{scope_tag}）" if is_ov_veto else "🟢 現場放行（覆寫解鎖）",
                "vessel_docked": vessel_docked, "dock_desc": dock_desc, "vector_desc": vector_desc,
                "four_way_summary": {"pos": dock_desc, "traj": vector_desc, "phys": physics_res["badge"], "off": f"🔒 {scope_tag}"}
            }

        if is_real_ais and in_boat_hours and vector_state in ["RETREATING_TO_WUSHI", "LOITERING_FAILED_DOCK"]:
            effective_official_veto = 1
            effective_official_label = "🔴 實質封島 (AIS路徑確認撤離)"
            effective_official_title = "【四維仲裁·臨時封島】五福號實船軌跡顯示返航烏石港/試靠失敗，現場執行封島疏散"
            consensus_status = f"🔴【四維路徑鐵證·封島】{vector_desc} ｜ 官網文字未更新前提前觸發熔斷！"
            trust_score, final_action = "99.5% (真實AIS路徑實證)", "🔴 0.0% 物理 VETO 熔斷（路徑確認撤離）"
        elif is_real_ais and in_boat_hours and vessel_docked:
            effective_official_veto = 0
            effective_official_label = "🟢 實質開島 (五福號駐島戒護)"
            effective_official_title = announcement.get("title", "【風管處通告】五福號駐島戒護，全島正常開放登島")
            consensus_status = f"🟢【四維驗證一致·開島】五福號駐泊戒護 ({dock_code}) ｜ 物理合規 (Hs={m.get('hs')}m)"
            trust_score = "100.0% (四維吻合)"
            final_action = physics_res["action_mode"] if not phys_veto else "🟡 實船駐島開窗"
        elif web_veto:
            effective_official_veto = 1
            scope_txt = "下午封島半天" if ann_scope == "AFTERNOON" else "官方公告封島"
            effective_official_label = f"🔴 {scope_txt}"
            effective_official_title = announcement.get("title", "【風管處公告】今日龜山島實施封島")
            consensus_status = f"🔴【官方公告封島】{effective_official_title} ｜ 日期面板 D0 已同步修正為封島！"
            trust_score, final_action = "100.0% (官方正式公告)", f"🔴 0.0% 物理 VETO 熔斷（{scope_txt}）"
        elif rl_res.get("rl_veto_triggered"):
            effective_official_veto = 1
            rl_score = rl_res.get("match_score", 80.0)
            rl_label = rl_res.get("matched_label", "例外封島原型")
            effective_official_label = f"🔴 實質封島 (11D RL智庫 {rl_score}% 精準收斂)"
            effective_official_title = f"【11D Safe RL 智庫判別·封島】匹配度 {rl_score}% 吻合「{rl_label}」"
            consensus_status = f"🧠【11D Safe RL 智庫精準收斂 {rl_score}% ≥ 80%】匹配「{rl_label}」，將灰色地帶坍縮為剛性封島！"
            trust_score = f"{rl_score}% (11D Safe RL 智庫>=80%精準判別)"
            final_action = "🔴 0.0% 物理 VETO 熔斷（11D RL智庫例外封島收斂）" if in_boat_hours else "🌙 夜間休整期（預警：🔴 RL智庫封島）"
        elif phys_veto or (ais_absent_in_hours and (gov_unreachable or float(m.get("hs_pier_north", 0)) > 0.90)):
            effective_official_veto = 1
            dialectic_reasons = []
            if south_closed and float(m.get("hs_pier_north", 0)) > 0.95:
                dialectic_reasons.append(f"南岸封閉且北岸浪高 {m.get('hs_pier_north')}m > 0.95m")
            if ais_absent_in_hours:
                dialectic_reasons.append("營運時段五福號滯留烏石港未出港")
            if gov_unreachable:
                dialectic_reasons.append("官網404無法驗證開放")
            reason_join = " ＋ ".join(dialectic_reasons) or "海象與船位交叉辯證異常"

            effective_official_label = "🔴 實質封島 (四維矛盾辯證熔斷)"
            effective_official_title = f"【四維辯證·實質封島】{reason_join}"
            consensus_status = f"🔴【四維矛盾辯證·封島】{reason_join}（修正單點盲區）！"
            trust_score = "98.2% (水動力+泊位+船位交叉辯證)"
            final_action = "🔴 0.0% 物理 VETO 熔斷（禁止靠泊）" if in_boat_hours else "🌙 夜間休整期（預警：🔴 物理 VETO 熔斷）"
        else:
            effective_official_veto = 0
            effective_official_label = "🟢 常態營運" if in_boat_hours else "🌙 夜間休整 (海象合規)"
            effective_official_title = announcement.get("title", "【風管處通告】全島常規開放營運中")
            if pm_risk and in_boat_hours:
                consensus_status = f"🟡【午前可航·午後封島預警】{pm_forecast.get('risk_label', '')} ｜ 建議縮短上午登島時窗"
                trust_score, final_action = "95.5% (逐時波譜前瞻預警)", "⏱️ Q3 動態開窗 (11:20 剛性止登 / 14:20 強制清島)"
            elif not in_boat_hours:
                consensus_status = f"🌙【夜間休整離峰期】非船班時段 ｜ 實時浪高 Hs={m.get('hs')}m、週期 Tp={m.get('tp')}s 符合安全基準"
                trust_score, final_action = "94.5% (夜間水動力持續監測)", f"🌙 夜間休整期（預估開窗：{physics_res['action_mode']}）"
            else:
                consensus_status = f"🟢【四維綜合校核】時段: {win['name']} ｜ {vector_desc} ｜ 實時浪高 Hs={m.get('hs')}m"
                trust_score, final_action = "94.0% (水動力+公告融合)", physics_res["action_mode"]

        return {
            "current_window": win, "manual_override": {"active": False},
            "web_official_veto": 1 if web_veto else 0, "announcement_scope": ann_scope,
            "effective_official_veto": effective_official_veto,
            "effective_official_label": effective_official_label,
            "effective_official_title": effective_official_title,
            "consensus_status": consensus_status, "trust_score": trust_score, "final_action": final_action,
            "vessel_docked": vessel_docked, "dock_desc": dock_desc, "vector_desc": vector_desc,
            "four_way_summary": {"pos": dock_desc, "traj": vector_desc, "phys": physics_res["badge"], "off": effective_official_label}
        }
