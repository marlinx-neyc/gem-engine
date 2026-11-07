class GemIntelligenceDB:
    def match_historical_event(self, telemetry: dict) -> dict:
        is_high_wave = telemetry.get("hs", 0) > 1.5
        return {
            "match_score": 88.5 if is_high_wave else 39.8,
            "is_alert": is_high_wave,
            "est_closure_days": 1 if is_high_wave else 0,
            "event_name": "2025 長湧衰退與大潮重疊" if is_high_wave else "常態海象",
            "lesson": "長浪共振防波堤消能瓦解，引橋漫頂全線封閉" if is_high_wave else "常態物理評估"
        }
