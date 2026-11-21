import os
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

CST = timezone(timedelta(hours=8))

class GemMacroRLOrchestrator:
    def __init__(self, intel_db_path: str = "data/calibrated_intel_db.json"):
        self.intel_db_path = intel_db_path
        self.feature_scales = {
            "hs": (0.45, 0.18),
            "tp": (2.50, 0.12),
            "weff": (3.00, 0.10),
            "pressure_3h": (1.00, 0.08),
            "tide": (0.45, 0.04),
            "south_closed": (0.50, 0.10),
            "wufu_in_port": (0.50, 0.10),
            "q_heaven_tide": (0.28, 0.07),
            "q_earth_berth": (0.28, 0.07),
            "q_human_gate": (0.28, 0.07),
            "q_deity_anomaly": (0.28, 0.07),
        }

    def _load_cases(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.intel_db_path):
            try:
                with open(self.intel_db_path, "r", encoding="utf-8") as f:
                    return json.load(f).get("historical_cases", [])
            except Exception:
                pass
        return []

    @staticmethod
    def _get_solar_term_dun(dt: datetime) -> str:
        m, d = dt.month, dt.day
        md = m * 100 + d
        dun = "陽遁" if (1221 <= md or md <= 620) else "陰遁"
        terms = [
            (105, "小寒"), (120, "大寒"), (204, "立春"), (219, "雨水"),
            (305, "驚蟄"), (320, "春分"), (404, "清明"), (420, "穀雨"),
            (505, "立夏"), (521, "小滿"), (605, "芒種"), (621, "夏至"),
            (707, "小暑"), (722, "大暑"), (807, "立秋"), (823, "處暑"),
            (907, "白露"), (923, "秋分"), (1008, "寒露"), (1023, "霜降"),
            (1107, "立冬"), (1122, "小雪"), (1207, "大雪"), (1221, "冬至")
        ]
        cur_term = "冬至"
        for t_md, t_name in terms:
            if md >= t_md:
                cur_term = t_name
        yuan = "上元" if (d % 15) in [1, 2, 3, 4, 5] else ("中元" if (d % 15) in [6, 7, 8, 9, 10] else "下元")
        return f"{dun}·{cur_term}{yuan}"

    def _synthesize_qimen_tensor(
        self,
        live_telemetry: Dict[str, Any],
        physics_metrics: Dict[str, Any],
        vessel_res: Dict[str, Any],
        dt: datetime
    ) -> Dict[str, Any]:
        hs = float(physics_metrics.get("hs", live_telemetry.get("hs", 1.0)))
        tp = float(physics_metrics.get("tp", live_telemetry.get("tp", 8.0)))
        hs_n = float(physics_metrics.get("hs_pier_north", hs * 0.883))
        weff = float(physics_metrics.get("weff", 4.0))
        p3h = float(physics_metrics.get("pressure_3h", live_telemetry.get("pressure_3h", 0.0)))
        tide = float(physics_metrics.get("tide", live_telemetry.get("tide", 0.9)))
        cv_rate = max(float(physics_metrics.get("cv_rate", 0.0)), float(live_telemetry.get("cctv_cv_rate", 0.0)))
        ukc_n = float(physics_metrics.get("ukc_north", 6.0))
        fb_n = float(physics_metrics.get("fb_north", 2.0))
        ann = live_telemetry.get("official_announcement", {})
        south_closed = bool(ann.get("south_pier_closed_damage", True))
        wufu = vessel_res.get("official_wufu", {})
        in_boat_hours = bool(wufu.get("in_boat_hours", True))
        is_docked = bool(wufu.get("is_docked_island", False))
        vec_state = wufu.get("vector_state", "")

        q_heaven = min(1.0, max(0.0, 0.45 * (hs / 2.2) + 0.35 * (max(0.0, tp - 5.0) / 10.0) + 0.20 * (abs(tide - 0.8) / 1.0)))
        star_tag = "天蓬/天芮長湧浪衝擊" if (tp >= 11.5 or hs >= 1.4) else ("天心/天輔平穩" if hs <= 0.95 else "天柱/天英湧動")

        berth_factor = 0.0 if (south_closed and hs_n > 0.95) else (0.65 if south_closed else 1.0)
        geom_margin = min(1.0, max(0.0, 0.5 * min(1.0, ukc_n / 3.0) + 0.5 * min(1.0, fb_n / 1.5)))
        q_earth = round(min(1.0, max(0.05, berth_factor * geom_margin)), 3)
        palace_tag = "離宮災損＋艮宮壓線" if (south_closed and hs_n > 0.95) else ("離宮災損·坎北單線" if south_closed else "坎離雙岸暢通")

        if not in_boat_hours:
            q_human = 0.15
            gate_tag = "休門（夜間非營運休整）"
        elif (south_closed and hs_n > 0.95) or weff > 10.17:
            q_human = 0.15
            gate_tag = "死門/驚門（泊位封閉禁航）"
        elif hs_n > 0.85 or weff > 7.5:
            q_human = 0.40
            gate_tag = "傷門/杜門（臨界觀望）"
        else:
            q_human = 0.88
            gate_tag = "開門/生門（適航開窗）"

        baro_shock = min(1.0, max(0.0, -p3h / 2.2))
        cv_shock = min(1.0, cv_rate / 2.0)
        ais_shock = 0.85 if vec_state in ["RETREATING_TO_WUSHI", "LOITERING_FAILED_DOCK"] else (0.65 if (in_boat_hours and not is_docked) else 0.10)
        q_deity = round(min(1.0, max(0.05, 0.40 * baro_shock + 0.25 * cv_shock + 0.35 * ais_shock)), 3)
        deity_tag = "白虎/騰蛇（氣壓驟降或船位異常）" if q_deity >= 0.65 else ("玄武/九地（潛在變數）" if q_deity >= 0.40 else "值符/六合（氣場穩定）")

        dun_str = self._get_solar_term_dun(dt)
        summary = f"{dun_str}｜{palace_tag}｜{gate_tag.split('（')[0]}｜{deity_tag.split('（')[0]}"

        return {
            "qimen_vector": {
                "q_heaven_tide": round(q_heaven, 3),
                "q_earth_berth": q_earth,
                "q_human_gate": round(q_human, 3),
                "q_deity_anomaly": q_deity
            },
            "qimen_summary": summary,
            "qimen_heaven": f"{dun_str} · {star_tag} (張量={q_heaven:.2f}, Hs={hs:.2f}m, Tp={tp:.1f}s)",
            "qimen_earth": f"{palace_tag} (承載度={q_earth:.2f}, 北岸Hs={hs_n:.2f}m, UKC={ukc_n:.2f}m)",
            "qimen_gate": f"{gate_tag} (通行度={q_human:.2f}, Weff={weff:.2f}m/s)",
            "qimen_deity": f"{deity_tag} (突變度={q_deity:.2f}, ΔP3h={p3h:+.1f}hPa, CV={cv_rate:.1f})"
        }

    def _compute_similarity_pct(self, cur: Dict[str, float], case: Dict[str, Any]) -> float:
        weighted_sq_dist = 0.0
        total_w = 0.0
        for feat, (scale, w) in self.feature_scales.items():
            v1 = float(cur.get(feat, 0.0))
            v2 = float(case.get(feat, v1))
            diff = (v1 - v2) / scale
            weighted_sq_dist += w * (diff ** 2)
            total_w += w
        norm_dist = math.sqrt(weighted_sq_dist / max(1e-6, total_w))
        raw_sim = math.exp(-0.55 * (norm_dist ** 2))
        rl_boost = min(1.06, max(0.92, float(case.get("weight", 1.0)) ** 0.25))
        return round(min(99.5, raw_sim * rl_boost * 100.0), 1)

    def evaluate_rl_match_with_hysteresis(
        self,
        live_telemetry: Dict[str, Any],
        physics_metrics: Dict[str, Any] = None,
        vessel_res: Dict[str, Any] = None,
        dt: datetime = None
    ) -> Dict[str, Any]:
        dt = dt or datetime.now(CST)
        physics_metrics = physics_metrics or {}
        vessel_res = vessel_res or {}
        wufu = vessel_res.get("official_wufu", {})
        ann = live_telemetry.get("official_announcement", {})

        qimen_matrix = self._synthesize_qimen_tensor(live_telemetry, physics_metrics, vessel_res, dt)
        qv = qimen_matrix["qimen_vector"]

        cur_vec = {
            "hs": float(physics_metrics.get("hs", live_telemetry.get("hs", 1.0))),
            "tp": float(physics_metrics.get("tp", live_telemetry.get("tp", 8.0))),
            "weff": float(physics_metrics.get("weff", 4.0)),
            "pressure_3h": float(physics_metrics.get("pressure_3h", live_telemetry.get("pressure_3h", 0.0))),
            "tide": float(physics_metrics.get("tide", live_telemetry.get("tide", 0.9))),
            "south_closed": 1.0 if ann.get("south_pier_closed_damage", True) else 0.0,
            "wufu_in_port": 0.0 if wufu.get("is_docked_island", False) else 1.0,
            "q_heaven_tide": qv["q_heaven_tide"],
            "q_earth_berth": qv["q_earth_berth"],
            "q_human_gate": qv["q_human_gate"],
            "q_deity_anomaly": qv["q_deity_anomaly"],
        }

        cases = self._load_cases()
        if not cases:
            return {
                "match_score": 0.0, "has_suggestion": False, "is_decisive_80": False,
                "rl_veto_triggered": False, "rl_open_triggered": False,
                "matched_category": "NONE", "matched_label": "智庫初始化中",
                "suggestion": "智庫初始化中", "qimen_matrix": qimen_matrix
            }

        scored = []
        for c in cases:
            sim = self._compute_similarity_pct(cur_vec, c)
            scored.append((sim, c))
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_case = scored[0]
        is_decisive = best_score >= 80.0
        matched_veto = int(best_case.get("veto", 0)) == 1
        cat = best_case.get("category", "UNKNOWN")
        cat_label = best_case.get("label", "歷史案例")

        if is_decisive and matched_veto:
            msg = f"🔴 11D Safe RL 智庫精準收斂 ({best_score}% >= 80%)：高度吻合【{cat_label}】，灰色地帶坍縮為 VETO 封島！"
        elif is_decisive and not matched_veto:
            msg = f"🟢 11D Safe RL 智庫精準收斂 ({best_score}% >= 80%)：高度吻合【{cat_label}】，支援安全開窗作業。"
        else:
            msg = f"🟡 11D Safe RL 智庫觀望 ({best_score}% < 80%)：最接近【{cat_label}】，交由物理與船位繼續交叉檢核。"

        return {
            "match_score": best_score,
            "has_suggestion": True,
            "is_decisive_80": is_decisive,
            "rl_veto_triggered": bool(is_decisive and matched_veto),
            "rl_open_triggered": bool(is_decisive and not matched_veto),
            "matched_category": cat,
            "matched_case_id": best_case.get("case_id", ""),
            "matched_label": cat_label,
            "suggestion": msg,
            "qimen_matrix": qimen_matrix
        }
