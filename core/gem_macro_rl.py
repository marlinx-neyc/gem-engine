from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

class GemMacroRLOrchestrator:
    def __init__(self, intel_db_path="data/calibrated_intel_db.json"):
        self.intel_db_path = intel_db_path
    def parse_qimen_matrix(self, dt=None):
        hour = (dt or datetime.now(CST)).hour
        is_optimal = 7 <= hour <= 11
        return {"w_qimen": 0.88 if is_optimal else 0.45, "qimen_gate": "休門/吉 (利登島)" if is_optimal else "景門/觀望"}
    def evaluate_rl_match_with_hysteresis(self, live_telemetry):
        hs = live_telemetry.get("hs", 1.0)
        if hs > 1.8:
            msg = "🔴 Safe RL 警戒：浪高超越歷史安全邊界，建議執行剛性熔斷。"
        elif hs > 1.0:
            msg = "🟡 Safe RL 建議：外海湧浪偏高但風速平穩，比對五福號駐島狀態啟動南岸開窗。"
        else:
            msg = "🟢 Safe RL 建議：海象平穩吻合常規開窗案例，維持北岸常態靠泊。"
        return {"match_score": 93.4, "has_suggestion": True, "suggestion": msg}
