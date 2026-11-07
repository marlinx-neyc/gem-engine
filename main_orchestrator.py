# -*- coding: utf-8 -*-
import os
import json
from utils.encoder import NpEncoder
from agents.gem_scout import GemScoutAgent
from agents.gem_cctv import GemCCTVPatternAgent
from agents.gem_vessel import GemVesselAgent
from agents.gem_signal import GemSignalAgent
from core.gem_physics import GemPhysicsEngine
from core.gem_intel import GemIntelligenceDB
from core.gem_calibration import GemCalibrationEngine

class GemConsensusOrchestrator:
    def __init__(self):
        self.scout = GemScoutAgent()
        self.cctv = GemCCTVPatternAgent()
        self.vessel = GemVesselAgent()
        self.physics = GemPhysicsEngine()
        self.intel = GemIntelligenceDB()
        self.calibration = GemCalibrationEngine()
        self.signal = GemSignalAgent()

    def execute_pipeline(self, raw_telemetry: dict = None):
        telemetry = self.scout.harvest_telemetry(raw_telemetry)
        announcement = telemetry["official_announcement"]

        cctv_res = self.cctv.process_cctv_frame_features({"cctv_cv_rate": telemetry["cctv_cv_rate"]})
        vessel_res = self.vessel.track_and_back_calculate(telemetry)

        intel_res = self.intel.match_historical_event(telemetry)
        physics_res = self.physics.evaluate_physics(telemetry, cctv_res)

        rl_feedback = self.calibration.process_double_q_per_feedback(
            actual_official_veto=announcement["official_veto"],
            predicted_action=0 if physics_res["hard_veto"] else 1
        )

        if announcement["official_veto"] == 1 or physics_res["hard_veto"]:
            final_action = "🔴 全線剛性熔斷（禁止靠泊）"
            badge = "🔴 0.0% 物理 VETO 熔斷"
        else:
            final_action = "🟢 常態開放靠泊"
            badge = "🟢 100.0% Q1 全線開放"

        live_payload = self.signal.package_live_status(
            physics_res, intel_res, rl_feedback, final_action, announcement, vessel_res
        )

        os.makedirs("data", exist_ok=True)
        with open("data/live_status.json", "w", encoding="utf-8") as f:
            json.dump(live_payload, f, cls=NpEncoder, ensure_ascii=False, indent=2)

        # 同時注入數據至根目錄 index.html 與 web/index.html 以確保 GitHub Pages 與 Colab 面板同步
        for target_path in ["index.html", "web/index.html"]:
            try:
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    json_str = json.dumps(live_payload, cls=NpEncoder, ensure_ascii=False)
                    if "window.INITIAL_LIVE_DATA = null;" in html_content:
                        injected_html = html_content.replace(
                            "window.INITIAL_LIVE_DATA = null;",
                            f"window.INITIAL_LIVE_DATA = {json_str};"
                        )
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(injected_html)
            except Exception:
                pass

        return {
            "badge": badge,
            "final_action": final_action,
            "vessel_res": vessel_res,
            "intel_res": intel_res,
            "physics_res": physics_res,
            "rl_feedback": rl_feedback
        }

if __name__ == "__main__":
    orchestrator = GemConsensusOrchestrator()
    res = orchestrator.execute_pipeline()
    print("🎯 管線執行完畢，最終裁示:", res["final_action"])
