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
            "hs": (0.45, 0.24),
            "tp": (2.50, 0.16),
            "weff": (3.00, 0.14),
            "pressure_3h": (1.00, 0.12),
            "tide": (0.45, 0.06),
            "south_closed": (0.50, 0.14),
            "wufu_in_port": (0.50, 0.14),
        }

    def _load_cases(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.intel_db_path):
            try:
                with open(self.intel_db_path, "r", encoding="utf-8") as f:
                    return json.load(f).get("historical_cases", [])
            except Exception:
                pass
        return []

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
        vessel_res: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        physics_metrics = physics_metrics or {}
        vessel_res = vessel_res or {}
        wufu = vessel_res.get("official_wufu", {})
        ann = live_telemetry.get("official_announcement", {})

        cur_vec = {
            "hs": float(physics_metrics.get("hs", live_telemetry.get("hs", 1.0))),
            "tp": float(physics_metrics.get("tp", live_telemetry.get("tp", 8.0))),
            "weff": float(physics_metrics.get("weff", 4.0)),
            "pressure_3h": float(physics_metrics.get("pressure_3h", live_telemetry.get("pressure_3h", 0.0))),
            "tide": float(physics_metrics.get("tide", live_telemetry.get("tide", 0.9))),
            "south_closed": 1.0 if ann.get("south_pier_closed_damage", True) else 0.0,
            "wufu_in_port": 0.0 if wufu.get("is_docked_island", False) else 1.0,
        }

        cases = self._load_cases()
        if not cases:
            return {
                "match_score": 0.0, "has_suggestion": False, "rl_veto_triggered": False,
                "matched_category": "NONE", "suggestion": "智庫初始化中"
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
            msg = f"🔴 Safe RL 智庫精準收斂 ({best_score}% >= 80%)：高度吻合【{cat_label}】，灰色地帶坍縮為 VETO 封島！"
        elif is_decisive and not matched_veto:
            msg = f"🟢 Safe RL 智庫精準收斂 ({best_score}% >= 80%)：高度吻合【{cat_label}】，支援安全開窗作業。"
        else:
            msg = f"🟡 Safe RL 智庫觀望 ({best_score}% < 80%)：最接近【{cat_label}】，交由物理與船位繼續交叉檢核。"

        return {
            "match_score": best_score,
            "has_suggestion": True,
            "is_decisive_80": is_decisive,
            "rl_veto_triggered": bool(is_decisive and matched_veto),
            "rl_open_triggered": bool(is_decisive and not matched_veto),
            "matched_category": cat,
            "matched_case_id": best_case.get("case_id", ""),
            "matched_label": cat_label,
            "suggestion": msg
        }
