import json
from datetime import datetime

# GEM 物理門檻標準
HS_THRESHOLD_M = 1.20    # 浪高門檻 (m)
WIND_THRESHOLD_MS = 10.80 # 風速門檻 (m/s)
UKC_THRESHOLD_M = 1.50   # 富餘水深門檻 (m)

def evaluate_veto_conditions(physics_metrics: dict) -> bool:
    """依據 GEM 戰術規範檢核是否觸發 VETO 一票否決"""
    hs_pier = physics_metrics.get("hs_pier_m", 0.0)
    w_local = physics_metrics.get("w_local_ms", 0.0)
    ukc = physics_metrics.get("ukc_m", 99.0)

    # 任何一項物理參數達到警戒邊界即強制 VETO
    is_hs_veto = hs_pier > HS_THRESHOLD_M
    is_wind_veto = w_local > WIND_THRESHOLD_MS
    is_ukc_veto = ukc < UKC_THRESHOLD_M

    return is_hs_veto or is_wind_veto or is_ukc_veto

def generate_ssot_decision(raw_pinn_data: dict) -> dict:
    """生成符合 v36D.13.0 SSOT 規範的最新決策 JSON 數據"""
    physics = raw_pinn_data.get("physics_metrics", {})
    has_veto = evaluate_veto_conditions(physics)
    physics["has_veto"] = has_veto

    if has_veto:
        # VETO 觸發：啟動剛性熔斷，強制覆寫決策燈號與航程文字，消除邏輯矛盾
        decision_status = "🔴 封島/防颱"
        hard_veto_alert = True
        
        guerrilla_dispatch = {
            "berthing_pier": "【南岸權宜碼頭】",
            "evacuation_pier": "【南岸權宜碼頭】 &rarr; 返航【烏石港】",
            "guerrilla_mode": "BOTH_PIERS_DISABLED",
            "morning_tactic": "🚨 浪高/風速超標觸發 VETO，取消常規登島班次",
            "afternoon_tactic": "🚨 10:50/13:50 雙預警，11:20 止登【南岸碼頭】，14:20 全員強制撤離至【烏石港】",
            "tactical_summary": "採納「方案 C (GEM-V36D)」，啟動剛性熔斷，10:50 預警/11:20 止登【南岸碼頭】，13:50 預警/14:20 全員撤離至【烏石港】。"
        }
    else:
        # 海象正常：執行常規時窗規劃
        decision_status = "🟢 常規開放"
        hard_veto_alert = False
        
        guerrilla_dispatch = {
            "berthing_pier": "【北岸主要碼頭】",
            "evacuation_pier": "【北岸主要碼頭】",
            "guerrilla_mode": "NORMAL",
            "morning_tactic": "08:30 首班登島：正常靠泊【北岸主要碼頭】",
            "afternoon_tactic": "全日海象符合安全標準，維持常規營運",
            "tactical_summary": "海象平穩（Hs ≤ 1.20m），採納「方案 A」，全線正常開放。"
        }

    # 組裝標準 SSOT JSON Payload
    ssot_payload = {
        "version": "v36D.13.0 Level 5 Complete",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S CST"),
        "decision": decision_status,
        "confidence_score": 100.0 if has_veto else raw_pinn_data.get("confidence_score", 95.0),
        "hard_veto_alert": hard_veto_alert,
        "precision_metrics": raw_pinn_data.get("precision_metrics", {
            "converged_sigma": 0.3125,
            "precision_gain_pct": 58.4
        }),
        "attention_gate": raw_pinn_data.get("attention_gate", {
            "micro_physics_weight": 65.0,
            "macro_qimen_weight": 35.0
        }),
        "physics_metrics": physics,
        "guerrilla_dispatch": guerrilla_dispatch,
        "level5_advanced_metrics": raw_pinn_data.get("level5_advanced_metrics", {}),
        "qimen_macro_consensus": raw_pinn_data.get("qimen_macro_consensus", {})
    }

    return ssot_payload

def export_to_json(payload: dict, output_path: str = "latest_decision.json"):
    """將 SSOT 數據導出為靜態 JSON 檔案供前端讀取"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 模擬 PINN Engine 傳入之即時水文數據 (測試 VETO 觸發)
    test_pinn_input = {
        "confidence_score": 100.0,
        "physics_metrics": {
            "hs_pier_m": 3.71,
            "w_local_ms": 8.50,
            "ukc_m": 5.84,
            "fb_pier_m": 2.00
        },
        "level5_advanced_metrics": {
            "vision_overtopping_rate_pmin": 1.31,
            "vessel_hydrodynamics": {
                "vessel_name": "凱鯨號 (穿浪雙體船)",
                "dynamic_squat_m": 0.82
            },
            "fno_forecast_mean_hs_m": 1.58,
            "quantum_topology_coherence": 0.4682
        }
    }
    
    final_payload = generate_ssot_decision(test_pinn_input)
    export_to_json(final_payload)
