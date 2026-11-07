# -*- coding: utf-8 -*-
import numpy as np
import json
import os
from datetime import datetime

class GemMacroRLOrchestrator:
    def __init__(self, intel_db_path="data/calibrated_intel_db.json"):
        self.intel_db_path = intel_db_path
        self.high_threshold = 0.80  # 80% 觸發建議門檻
        self.low_threshold = 0.72   # 72% 滯後釋放門檻
        self.last_state_active = False

    def parse_qimen_matrix(self, dt: datetime = None) -> dict:
        """將時間與方位映射至奇門戰術矩陣權重 W_qimen"""
        dt = dt or datetime.now()
        hour = dt.hour
        is_optimal = 7 <= hour <= 11
        qimen_score = 0.88 if is_optimal else 0.45
        return {
            "w_qimen": qimen_score,
            "qimen_gate": "休門/吉 (利登島)" if is_optimal else "景門/平 (觀望)",
            "shield_angle_deg": 210.0  # 南岸背風角
        }

    def downscale_macro_api(self, macro_data: dict, qimen_res: dict) -> dict:
        """外海深水波與風場降尺度至局部碼頭水動力"""
        hs_deep = macro_data.get("hs_deep", 1.80)
        tp_deep = macro_data.get("tp_deep", 10.5)
        w_macro = macro_data.get("w_macro", 12.0)
        monsoon_angle = macro_data.get("monsoon_angle", 50.0)

        # 碼頭地形與繞射折減
        kd_north = 1.00 if monsoon_angle < 60 else 0.75
        kd_south = 0.55

        return {
            "hs_north": round(hs_deep * kd_north, 2),
            "hs_south": round(hs_deep * kd_south, 2),
            "weff": round(w_macro * abs(np.cos(np.radians(monsoon_angle - 45.0))), 2),
            "tp": tp_deep,
            "w_qimen": qimen_res["w_qimen"]
        }

    def evaluate_rl_match_with_hysteresis(self, live_telemetry: dict) -> dict:
        """80%/72% 雙向滯後 Safe RL 戰術建議引擎"""
        if not os.path.exists(self.intel_db_path):
            return {"match_score": 0.0, "has_suggestion": False, "suggestion": "智庫建置中"}

        with open(self.intel_db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        cases = db.get("historical_cases", [])
        current_vec = np.array([
            live_telemetry.get("hs", 1.0),
            live_telemetry.get("tp", 8.0),
            live_telemetry.get("w", 6.0),
            live_telemetry.get("tide", 1.0)
        ])

        best_sim = -1.0
        best_case = None

        for case in cases:
            case_vec = np.array([case["hs"], case["tp"], case["w"], case["tide"]])
            dist = np.linalg.norm(current_vec - case_vec)
            sim = 1.0 / (1.0 + dist)
            if sim > best_sim:
                best_sim = sim
                best_case = case

        match_score = round(best_sim * 100, 1)

        # 雙向滯後鎖定邏輯
        if self.last_state_active:
            active = (best_sim >= self.low_threshold)
        else:
            active = (best_sim >= self.high_threshold)

        self.last_state_active = active

        if active and best_case:
            suggestion = (
                f"💡【80% RL 戰術智庫建議】: 吻合 {best_case['time']} 歷史避風案例 "
                f"(波高 {best_case['hs']}m / 烏石港避風率 {best_case.get('wushi_shelter_rate', 0)}%)。"
                f"建議處置：{best_case['action']}。"
            )
            return {
                "match_score": match_score,
                "has_suggestion": True,
                "suggestion": suggestion,
                "recommended_action": best_case["action"]
            }

        return {
            "match_score": match_score,
            "has_suggestion": False,
            "suggestion": f"目前海象與歷史案例匹配度為 {match_score}% (< 80%)，由物理剛性門檻進行主導控制。",
            "recommended_action": "常規監測"
        }
