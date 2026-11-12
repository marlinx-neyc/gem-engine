# -*- coding: utf-8 -*-
import os, json, re
from datetime import datetime, timedelta, timezone
from utils.encoder import NpEncoder
from tools.gem_historical_miner import GemHistoricalDataMiner
from core.gem_macro_rl import GemMacroRLOrchestrator
from agents.gem_scout import GemScoutAgent
from agents.gem_cctv import GemCCTVPatternAgent
from agents.gem_vessel import GemVesselAgent
from agents.gem_signal import GemSignalAgent
from core.gem_physics import GemPhysicsEngine
from core.gem_consensus import GemMultiSourceConsensus

CST = timezone(timedelta(hours=8))

def purge_and_atomic_write(target_filepath: str, new_payload: dict) -> None:
    target_dir = os.path.dirname(target_filepath) or "."
    os.makedirs(target_dir, exist_ok=True)
    tmp_filepath = f"{target_filepath}.tmp_{os.getpid()}_{datetime.now(CST).strftime('%f')}"
    with open(tmp_filepath, "w", encoding="utf-8") as f:
        json.dump(new_payload, f, cls=NpEncoder, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_filepath, target_filepath)

class GemConsensusOrchestrator:
    def __init__(self, cwa_key: str = None, fb_tok: str = None, fb_id: str = None):
        self.miner = GemHistoricalDataMiner()
        self.miner.generate_calibrated_intel_db()
        self.macro_rl = GemMacroRLOrchestrator()
        self.scout = GemScoutAgent(cwa_key, fb_tok, fb_id)
        self.cctv = GemCCTVPatternAgent()
        self.vessel = GemVesselAgent()
        self.physics = GemPhysicsEngine()
        self.consensus = GemMultiSourceConsensus()
        self.signal = GemSignalAgent()

    def execute_pipeline(self, raw_telemetry: dict = None):
        telemetry = self.scout.harvest_telemetry(raw_telemetry)
        announcement = telemetry["official_announcement"]
        swell_res = telemetry.get("swell_forecast", {})
        cctv_res = self.cctv.process_cctv_frame_features({"cctv_cv_rate": telemetry["cctv_cv_rate"]})
        vessel_res = self.vessel.track_and_back_calculate(telemetry)
        physics_res = self.physics.evaluate_physics(telemetry, cctv_res)

        consensus_res = self.consensus.arbitrate_consensus(
            announcement=announcement,
            vessel_res=vessel_res,
            physics_res=physics_res,
            cctv_res=cctv_res
        )

        final_action = consensus_res["final_action"]
        live_payload = self.signal.package_live_status(
            physics_res=physics_res,
            consensus_res=consensus_res,
            announcement=announcement,
            vessel_res=vessel_res,
            swell_res=swell_res,
            cctv_res=cctv_res,
            telemetry=telemetry
        )

        purge_and_atomic_write("data/live_status.json", live_payload)

        json_str = json.dumps(live_payload, cls=NpEncoder, ensure_ascii=False).replace("</script>", "<\\/script>")
        pattern = r'<script id="initial-live-data" type="application/json">[\s\S]*?</script>'
        replacement = f'<script id="initial-live-data" type="application/json">{json_str}</script>'

        for target_path in ["index.html", "web/index.html"]:
            try:
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    if re.search(pattern, html_content):
                        injected_html = re.sub(pattern, replacement, html_content, count=1)
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(injected_html)
            except Exception:
                pass

        return {
            "badge": consensus_res["trust_score"],
            "final_action": final_action,
            "vessel_status": consensus_res["dock_desc"],
            "effective_official": consensus_res["effective_official_label"],
            "consensus_status": consensus_res["consensus_status"],
            "physics_res": physics_res,
            "data_source": telemetry.get("data_source", "live")
        }

if __name__ == "__main__":
    res = GemConsensusOrchestrator().execute_pipeline()
    print("🎯 最終多重驗證裁示:", res["final_action"])
