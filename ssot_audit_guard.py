#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GEM-V36D 主動對齊修復型「掃兵」巡檢系統 (Active Auto-Repair Alignment Inspector)
================================================================================
最高技術規範對齊：GEM_SPEC_MASTER.md (v36D.330.0)
職責：全量巡檢 latest_decision.json 之 SSOT 數據一致性，主動排除四層物理防線、
奇門門控與游擊調度決策間之邏輯矛盾並進行零跳動寫回修復。
================================================================================
"""

import json
import sys
from typing import Dict, Any, Tuple

def auto_repair_and_align_ssot(file_path: str = "latest_decision.json") -> bool:
    print(f"🔍 啟動 GEM-V36D 自動對齊掃兵巡檢：{file_path} ...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 讀取 SSOT 檔案失敗: {e}")
        return False

    is_repaired = False
    physics = data.get("physics_metrics", {})
    dispatch = data.get("guerrilla_dispatch", {})
    qimen = data.get("qimen_macro_consensus", {})
    schemes = data.get("three_schemes_comparison", {})

    # 1. 奇門門控與 α_tune 自適應緊縮導正
    qimen_pct = qimen.get("consensus_rate_pct", 0.0)
    gate_state = qimen.get("octagram_gate_state", qimen.get("gate_state", ""))
    
    if qimen_pct >= 70.0 and any(k in gate_state for k in ["死門", "坤宮"]):
        target_alpha = 0.65
        if physics.get("alpha_tune") != target_alpha or physics.get("alpha_adaptive") != target_alpha:
            physics["alpha_tune"] = target_alpha
            physics["alpha_adaptive"] = target_alpha
            physics["eff_hs_limit"] = round(1.20 * target_alpha, 2)
            physics["eff_weff_limit"] = round(10.80 * target_alpha, 2)
            physics["hs_threshold_m"] = physics["eff_hs_limit"]
            is_repaired = True

    alpha = physics.get("alpha_adaptive", physics.get("alpha_tune", 0.94))
    hs_limit = physics.get("eff_hs_limit", physics.get("hs_threshold_m", round(1.20 * alpha, 2)))
    weff_limit = physics.get("eff_weff_limit", round(10.80 * alpha, 2))
    ukc_limit = physics.get("eff_ukc_limit", 1.50)
    fb_limit = physics.get("eff_fb_limit", 0.50)

    # 2. 四層 Hard VETO 剛性水文門檻全量檢核 (Hs, Weff, UKC, FB)
    hs_pier = physics.get("hs_pier_m", 0.0)
    w_eff = physics.get("w_eff_ms", physics.get("w_local_ms", 0.0))
    ukc = physics.get("ukc_m", 99.0)
    fb_pier = physics.get("fb_pier_m", 99.0)

    veto_hs = hs_pier > hs_limit
    veto_w = w_eff > weff_limit
    veto_ukc = ukc < ukc_limit
    veto_fb = fb_pier < fb_limit
    
    has_veto = veto_hs or veto_w or veto_ukc or veto_fb or physics.get("has_veto", False) or data.get("hard_veto_alert", False)

    # 導正四層子標籤狀態
    if physics.get("pass_hs") != (not veto_hs):
        physics["pass_hs"] = not veto_hs
        is_repaired = True
    if physics.get("pass_w") != (not veto_w):
        physics["pass_w"] = not veto_w
        is_repaired = True
    if physics.get("pass_ukc") != (not veto_ukc):
        physics["pass_ukc"] = not veto_ukc
        is_repaired = True
    if physics.get("pass_fb") != (not veto_fb):
        physics["pass_fb"] = not veto_fb
        is_repaired = True

    if has_veto and not physics.get("has_veto"):
        physics["has_veto"] = True
        is_repaired = True

    if has_veto and not data.get("hard_veto_alert"):
        data["hard_veto_alert"] = True
        is_repaired = True

    # 3. 硬熔斷狀態下之全局戰術一致性同步 (State Cascade)
    if has_veto:
        target_decision = "🔴 0.0% 物理 VETO 熔斷 / 全線封島"
        if data.get("decision") != target_decision:
            data["decision"] = target_decision
            is_repaired = True

        target_berthing = "無 (雙岸失效，禁止靠泊)"
        if dispatch.get("berthing_pier") != target_berthing:
            dispatch["berthing_pier"] = target_berthing
            is_repaired = True

        target_evac = "無 (雙岸失效，直航返航烏石港)"
        if dispatch.get("evacuation_pier") != target_evac:
            dispatch["evacuation_pier"] = target_evac
            is_repaired = True

        target_mode = "BOTH_PIERS_DISABLED"
        if dispatch.get("guerrilla_mode") != target_mode:
            dispatch["guerrilla_mode"] = target_mode
            is_repaired = True

        if "熔斷" not in dispatch.get("tactical_summary", ""):
            dispatch["tactical_summary"] = "🔴 第一位階 Hard VETO 剛性熔斷，全天禁止登島與靠泊"
            is_repaired = True

        # 同步方案 C (GEM Ground Truth)
        if "scheme_c_gem" in schemes:
            if schemes["scheme_c_gem"].get("status") != target_decision:
                schemes["scheme_c_gem"]["status"] = target_decision
                is_repaired = True

    # 4. 數據寫回與結果輸出
    if is_repaired:
        data["physics_metrics"] = physics
        data["guerrilla_dispatch"] = dispatch
        if schemes:
            data["three_schemes_comparison"] = schemes
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ [掃兵修復完成] 成功排除矛盾，已將修復後數據寫回 SSOT！")
    else:
        print("🟢 [掃兵巡檢通過] 數據三區塊無矛盾，符合 100% 一致性標準！")

    return True

if __name__ == "__main__":
    success = auto_repair_and_align_ssot()
    if not success:
        sys.exit(1)
