# -*- coding: utf-8 -*-
import numpy as np
import json
import os
from datetime import datetime

class GemMacroRLOrchestrator:
    def __init__(self, intel_db_path="data/calibrated_intel_db.json", q_table_path="data/q_table.json"):
        self.intel_db_path = intel_db_path
        self.q_table_path = q_table_path
        self.high_threshold = 0.80  # 80% 觸發門檻
        self.low_threshold = 0.72   # 72% 釋放門檻
        self.last_state_active = False
        self.lr = 0.1
        self.gamma = 0.9
        self.q_table = self._load_or_init_q_table()

    def _load_or_init_q_table(self) -> dict:
        if os.path.exists(self.q_table_path):
            try:
                with open(self.q_table_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def parse_qimen_matrix(self, dt: datetime = None) -> dict:
        """奇門戰術開窗權重 (W_qimen)"""
        dt = dt or datetime.now()
        hour = dt.hour
        is_optimal = 7 <= hour <= 11
        return {
            "w_qimen": 0.88 if is_optimal else 0.45,
            "qimen_gate": "休門/吉 (利登島)" if is_optimal else "景門/觀望"
        }

    def downscale_macro_api(self, macro_data: dict, qimen_res: dict) -> dict:
        """PINN 水動力簡化降尺度推算碼頭波高與折算風速"""
        hs_deep = macro_data.get("hs_deep", 1.80)
        tp_deep = macro_data.get("tp_deep", 10.5)
        w_macro = macro_data.get("w_macro", 12.0)
        monsoon_angle = macro_data.get("monsoon_angle", 50.0)

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
        """80%/72% 雙向滯後 Safe RL 檢索與戰術建議」"""
        if not os.path.exists(self.intel_db_path):
            return {"match_score": 0.0, "has_suggestion": False, "suggestion": "智庫建置中"}

        with open(self.intel_db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        cases = db.get("historical_cases", [])
        
        hs = live_telemetry.get("hs", 1.0)
        tp = live_telemetry.get("tp", 8.0)
        e_flux = hs**2 * tp
        w = live_telemetry.get("w", 6.0)
        tide = live_telemetry.get("tide", 1.0)

        current_vec = np.array([hs, tp, e_flux, w, tide])

        best_sim = -1.0
        best_case = None

        for case in cases:
            case_vec = np.array([case["hs"], case["tp"], case.get("energy_flux", case["hs"]**2 * case["tp"]), case["w"], case["tide"]])
            dist = np.linalg.norm(current_vec - case_vec)
            sim = 1.0 / (1.0 + dist)
            if sim > best_sim:
                best_sim = sim
                best_case = case

        match_score = round(best_sim * 100, 1)

        # 雙向滯後機制 (Hysteresis)
        if self.last_state_active:
            active = (best_sim >= self.low_threshold)
        else:
            active = (best_sim >= self.high_threshold)

        self.last_state_active = active

        if active and best_case:
            suggestion = (
                f"💡【80% Safe RL 戰術智庫建議】: 特徵高度吻合 {best_case['time']} 灰色地帶案例 "
                f"(波浪能量流 {best_case.get('energy_flux', 0)} / 船長共識 {best_case.get('captain_consensus', 0)})。"
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
            "suggestion": f"目前海象特徵與歷史案例匹配度為 {match_score}% (< 80%)，由物理剛性門檻進行控制。",
            "recommended_action": "常規監測"
        }

    def train_online_step(self, state_key: str, action: int, reward: float, next_state_key: str):
        """在線 Q-Learning 自主訓練更新」"""
        current_q = self.q_table.get(state_key, [0.0, 0.0, 0.0, 0.0])[action]
        max_next_q = max(self.q_table.get(next_state_key, [0.0, 0.0, 0.0, 0.0]))
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0, 0.0, 0.0, 0.0]
        self.q_table[state_key][action] = round(new_q, 4)

        os.makedirs("data", exist_ok=True)
        with open(self.q_table_path, "w", encoding="utf-8") as f:
            json.dump(self.q_table, f, ensure_ascii=False, indent=2)
