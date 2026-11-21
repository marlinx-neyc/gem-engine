import json
class GemSignalAgent:
    def package_live_status(self, physics_res, consensus_res, announcement, vessel_res, swell_res, cctv_res, telemetry):
        return {"decision": consensus_res["final_action"]}
