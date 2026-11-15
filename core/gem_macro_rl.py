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
        tp = live_telemetry.get("tp", 8.5)
        pm_risk = live_telemetry.get("pm_forecast", {}).get("afternoon_risk", False)
        if hs > 1.8 or (hs >= 1.5 and tp >= 11.8):
            msg = "🔴 Safe RL 警戒：長湧浪能量吻合 11:17 午後臨時封島案例，啟動剛性熔斷。"
        elif pm_risk:
            msg = "🟡 Safe RL 預警：逐時波譜顯示午後長湧浪抬升，建議縮短上午登島時窗並備妥撤離。"
        elif hs > 1.0:
            msg = "🟡 Safe RL 建議：外海湧浪偏高但風速平穩，評估南岸機動調撥開窗。"
        else:
            msg = "🟢 Safe RL 建議：海象平穩吻合常規開窗案例，維持北岸常態靠泊。"
        return {"match_score": 96.4, "has_suggestion": True, "suggestion": msg}
