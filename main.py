import json
import torch
import os
from datetime import datetime, timezone, timedelta
from main_orchestrator import (
    AutonomousDialecticalOrchestrator, 
    PrecisionConvergenceEngine, 
    UnifiedMarineTelemetry
)

def build_veto_reason_string(metrics: dict) -> str:
    """動態解析真正觸發 VETO 的精確物理原因 (修復數值判斷 Bug)"""
    triggers = []
    if metrics["hs_pier_m"] > 1.20:
        triggers.append(f"碼頭浪高 Hs ({metrics['hs_pier_m']}m > 1.20m)")
    if metrics["w_local_ms"] > 10.80:
        triggers.append(f"局部風速 W ({metrics['w_local_ms']}m/s > 10.80m/s)")
    if metrics["ukc_m"] < 1.50:
        triggers.append(f"富餘水深 UKC ({metrics['ukc_m']}m < 1.50m)")
    if metrics["fb_pier_m"] < 0.50:
        triggers.append(f"碼頭預留高度 Freeboard ({metrics['fb_pier_m']}m < 0.50m)")
        
    if triggers:
        return f"觸發剛性 VETO：{' 及 '.join(triggers)}"
    return "物理指標正常 (PASS)"

def fetch_cwa_and_run_pipeline():
    # 1. 載入最新 v36D.11.0 權重與精確度收斂引擎
    model_path = os.getenv("MODEL_PATH", "model_v36D.11.0.pt")
    orchestrator = AutonomousDialecticalOrchestrator(model_path=model_path)
    orchestrator.policy.eval()
    precision_engine = PrecisionConvergenceEngine(orchestrator)
    
    # 2. 帶入當前遙測數據 (以極端海象數據為例)
    telemetry = UnifiedMarineTelemetry(
        hs_cwa=3.23, w_cwa=13.50, tide_eta_m=1.20, 
        astro_tide_phase=0.95, future_3h_tide_surge_m=0.75, typhoon_dist_km=110.0
    )
    
    # 3. 執行相對精確度雙核收斂與 PINN 評估
    res = precision_engine(telemetry)
    norm_vec = orchestrator.extractor.build_normalized_vector(telemetry)
    pinn_metrics = orchestrator.pinn_engine.evaluate_physics(telemetry, norm_vec)
    
    # 修正 VETO 原因文字
    veto_reason = build_veto_reason_string(pinn_metrics)
    pinn_metrics["reason"] = veto_reason
    
    # 4. 封裝最新的 SSOT 規範結構 (v36D.11.0)
    payload = {
        "version": "v36D.11.0",
        "timestamp": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S CST"),
        "decision": res["decision"],
        "confidence_score": res["confidence_score"],
        "hard_veto_alert": res["physics_veto"],
        "veto_reason": veto_reason,
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
    
    # 5. 寫入 SSOT 狀態檔
    with open("latest_decision.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    print("✅ latest_decision.json 已成功更換為 v36D.11.0 規範並修正原因邏輯。")

if __name__ == "__main__":
    fetch_cwa_and_run_pipeline()
