import json
import torch
import os
from datetime import datetime, timezone, timedelta
from main_orchestrator import (
    AutonomousDialecticalOrchestrator, 
    PrecisionConvergenceEngine, 
    UnifiedMarineTelemetry
)

def fetch_cwa_and_run_pipeline():
    # 1. 載入最新 v36D.11.0 權重與精確度引擎
    model_path = os.getenv("MODEL_PATH", "model_v36D.11.0.pt")
    orchestrator = AutonomousDialecticalOrchestrator(model_path=model_path)
    orchestrator.policy.eval()
    precision_engine = PrecisionConvergenceEngine(orchestrator)
    
    # 2. 模擬或讀取實時 CWA 遙測數據 (可於日後串接實際 API)
    telemetry = UnifiedMarineTelemetry(
        hs_cwa=3.6, w_cwa=16.0, tide_eta_m=1.8, 
        astro_tide_phase=0.95, future_3h_tide_surge_m=0.75, typhoon_dist_km=110.0
    )
    
    # 3. 執行精確度收斂與 PINN 評估
    res = precision_engine(telemetry)
    norm_vec = orchestrator.extractor.build_normalized_vector(telemetry)
    pinn_metrics = orchestrator.pinn_engine.evaluate_physics(telemetry, norm_vec)
    
    # 4. 封裝 SSOT payload 供前端與 Dashboard 渲染
    payload = {
        "version": "v36D.11.0",
        "timestamp": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S CST"),
        "decision": res["decision"],
        "confidence_score": res["confidence_score"],
        "hard_veto_alert": res["physics_veto"],
        "precision_metrics": {
            "converged_sigma": res["converged_uncertainty_sigma"],
            "precision_gain_pct": res["precision_gain_pct"]
        },
        "attention_gate": {
            "micro_physics_weight": round((1.0 - res["w_macro"]) * 100, 1),
            "macro_qimen_weight": round(res["w_macro"] * 100, 1)
        },
        "physics_metrics": pinn_metrics,
        "telemetry_summary": {
            "hs_cwa": telemetry.hs_cwa,
            "w_cwa": telemetry.w_cwa,
            "tide_eta_m": telemetry.tide_eta_m,
            "future_3h_tide_surge_m": telemetry.future_3h_tide_surge_m
        }
    }
    
    # 5. 寫入單一真理源 json
    with open("latest_decision.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    print("✅ latest_decision.json 已成功產出 (v36D.11.0)。")

if __name__ == "__main__":
    fetch_cwa_and_run_pipeline()
