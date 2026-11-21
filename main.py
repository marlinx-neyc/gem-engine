# -*- coding: utf-8 -*-
import os, json, re, hashlib
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
    def __init__(self, cwa_key: str = None, fb_tok: str = None, fb_id: str = None, ais_url: str = None):
        self.miner = GemHistoricalDataMiner()
        self.miner.generate_calibrated_intel_db()
        self.macro_rl = GemMacroRLOrchestrator()
        self.scout = GemScoutAgent(cwa_key, fb_tok, fb_id)
        self.cctv = GemCCTVPatternAgent()
        self.vessel = GemVesselAgent(ais_api_url=ais_url)
        self.physics = GemPhysicsEngine()
        self.consensus = GemMultiSourceConsensus()
        self.signal = GemSignalAgent()

    def _load_existing_live_status(self) -> dict:
        for candidate in ["data/live_status.json", "latest_decision.json"]:
            if os.path.exists(candidate):
                try:
                    with open(candidate, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return {}

    @staticmethod
    def _compute_semantic_state_hash(payload: dict) -> str:
        m = payload.get("metrics", {})
        pm = payload.get("pm_forecast", {})
        sig_obj = {
            "decision": payload.get("decision"),
            "official_veto": payload.get("official_veto"),
            "web_official_veto": payload.get("web_official_veto"),
            "tomorrow_veto": payload.get("tomorrow_veto"),
            "announcement_scope": payload.get("announcement_scope"),
            "manual_override": payload.get("manual_override"),
            "wufu_status": payload.get("official_wufu_status"),
            "wufu_vector": payload.get("official_wufu_vector"),
            "afternoon_risk": pm.get("afternoon_risk", False),
            "hs_bucket": round(float(m.get("hs", 0.0)) / 0.05),
            "tp_bucket": round(float(m.get("tp", 0.0)) / 0.5)
        }
        raw = json.dumps(sig_obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def execute_pipeline(self, raw_telemetry: dict = None, force_write: bool = False):
        existing_state = self._load_existing_live_status()
        telemetry = self.scout.harvest_telemetry(raw_telemetry)
        announcement = telemetry["official_announcement"]
        swell_res = telemetry.get("swell_forecast", {})
        pm_fc = telemetry.get("pm_forecast", {})
        cctv_res = self.cctv.process_cctv_frame_features({
            "cctv_cv_rate": telemetry["cctv_cv_rate"],
            "tide": telemetry["tide"]
        })
        vessel_res = self.vessel.track_and_back_calculate(telemetry)
        physics_res = self.physics.evaluate_physics(telemetry, cctv_res)

        consensus_res = self.consensus.arbitrate_consensus(
            announcement=announcement, vessel_res=vessel_res, physics_res=physics_res,
            cctv_res=cctv_res, pm_forecast=pm_fc, existing_state=existing_state
        )

        final_action = consensus_res["final_action"]
        live_payload = self.signal.package_live_status(
            physics_res=physics_res, consensus_res=consensus_res, announcement=announcement,
            vessel_res=vessel_res, swell_res=swell_res, cctv_res=cctv_res, telemetry=telemetry
        )

        m_v665 = physics_res.get("metrics", {})
        ty_info = telemetry.get("typhoon_info", {})
        live_payload["spec_version"] = "GEM-ENG-SPEC-2026-V66.5-UNIFIED"
        live_payload["action_id"] = physics_res.get("action_id", 0)
        live_payload["decision_code"] = f"Q{physics_res.get('action_id', 0)}" if physics_res.get("action_id") in [1,2,3] else "Q4"
        live_payload["emergency_centers"] = ty_info.get("emergency_centers", {"central": "未開設", "yilan": "未開設", "new_taipei": "未開設"})
        live_payload["physics_metrics"] = {
            "hs_pier_m": m_v665.get("hs_pier_south", 0.0),
            "hs_pier_north_m": m_v665.get("hs_pier_north", 0.0),
            "w_local_ms": m_v665.get("weff", 0.0),
            "ukc_m": m_v665.get("ukc_south", 0.0),
            "ukc_north_m": m_v665.get("ukc_north", 0.0),
            "fb_pier_m": m_v665.get("fb_south", 0.0),
            "s_squat_m": m_v665.get("squat_south_3kt", 0.0),
            "s_squat_north_m": m_v665.get("squat_north", 0.0),
            "k_flux": m_v665.get("k_flux", 0.0),
            "v_impedance": m_v665.get("v_impedance", 0.0),
            "e_net": m_v665.get("e_net", 0.0),
            "p_veto": m_v665.get("p_veto", 0.0),
            "evac_minutes": m_v665.get("evac_minutes", 20),
            "milk_sea_peak": m_v665.get("milk_sea_peak", "13:30"),
            "has_veto": physics_res.get("hard_veto", False),
            "is_tier0": physics_res.get("is_tier0", False)
        }

        new_hash = self._compute_semantic_state_hash(live_payload)
        live_payload["state_hash"] = new_hash
        prev_hash = existing_state.get("state_hash", "")
        all_targets_exist = all(os.path.exists(p) for p in ["data/live_status.json", "latest_decision.json", "index.html"])

        skipped_write = False
        if not force_write and not raw_telemetry and all_targets_exist and new_hash == prev_hash:
            skipped_write = True
        else:
            purge_and_atomic_write("data/live_status.json", live_payload)
            purge_and_atomic_write("latest_decision.json", live_payload)

            json_str = json.dumps(live_payload, cls=NpEncoder, ensure_ascii=False).replace("</script>", "<\\/script>")
            pattern = r'<script id="initial-live-data" type="application/json">[\s\S]*?</script>'
            replacement = f'<script id="initial-live-data" type="application/json">{json_str}</script>'

            for target_path in ["index.html", "web/index.html", "mobile.html", "desktop.html"]:
                try:
                    if os.path.exists(target_path):
                        with open(target_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        if re.search(pattern, html_content):
                            injected_html = re.sub(pattern, lambda _: replacement, html_content, count=1)
                            with open(target_path, "w", encoding="utf-8") as f:
                                f.write(injected_html)
                except Exception:
                    pass

        return {
            "badge": consensus_res["trust_score"], "final_action": final_action,
            "vessel_status": consensus_res["dock_desc"], "vector_status": consensus_res["vector_desc"],
            "pm_risk_label": pm_fc.get("risk_label", ""), "effective_official": consensus_res["effective_official_label"],
            "consensus_status": consensus_res["consensus_status"], "physics_res": physics_res,
            "scraper_diagnostics": announcement.get("scraper_diagnostics", {}),
            "data_source": telemetry.get("data_source", "live"), "state_hash": new_hash[:12], "skipped_write": skipped_write
        }

if __name__ == "__main__":
    res = GemConsensusOrchestrator().execute_pipeline()
    print(f"🎯 最終四維多重驗證裁示: {res['final_action']} (HASH={res['state_hash']}, 略過無變動寫入={res['skipped_write']})")
