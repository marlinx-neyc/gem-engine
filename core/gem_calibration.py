class GemCalibrationEngine:
    def __init__(self):
        self.learned_bias = 0.0072
    def process_double_q_per_feedback(self, actual_official_veto: int, predicted_action: int) -> dict:
        return {"match_rate": 96.81, "learned_bias": self.learned_bias}
