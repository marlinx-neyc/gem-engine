#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GEM-V36D 主動對齊修復型「掃兵」巡檢系統 (Active Auto-Repair Alignment Inspector)
功能：掃描 SSOT Payload 與 UI 狀態，若發現任何「一邊熔斷、一邊開放」等衝突不一致，
     自動執行一票否決對齊修復 (Auto-Repair)，確保傳出訊息 100% 三者一致。
================================================================================
"""

import json
import sys

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

    hs_pier = physics.get("hs_pier_m", 0.0)
    hs_thresh = physics.get("hs_threshold_m", 0.78)
    has_veto = (hs_pier > hs_thresh) or physics.get("has_veto", False)

    # 1. 自動修正 VETO 標籤與門檻
    if has_veto and not physics.get("has_veto"):
        physics["has_veto"] = True
        is_repaired = True
        print("🛠️ [掃兵對齊] 自動修正: physics_metrics.has_veto -> True")

    # 2. 自動對齊奇門死門與 alpha_tune 緊縮
    if qimen.get("consensus_rate_pct", 0.0) >= 70.0 and qimen.get("octagram_gate_state", qimen.get("qimen_gate")) in ["死門", "死門 (坤宮 - 剛性熔斷)"]:
        if physics.get("alpha_tune") != 0.65:
            physics["alpha_tune"] = 0.65
            physics["hs_threshold_m"] = round(1.20 * 0.65, 2)
            is_repaired = True
            print("🛠️ [掃兵對齊] 自動修正: alpha_tune -> 0.65, hs_threshold_m -> 0.78m")

    # 3. 核心裁決與游擊調度三大區塊全域強制一致性對齊
    if has_veto:
        if "🔴" not in data.get("decision", "") or "封島" not in data.get("decision", ""):
            data["decision"] = "🔴 0.0% 物理 VETO 熔斷 / 全線封島"
            is_repaired = True
            print("🛠️ [掃兵對齊] 自動修復總裁決為: 🔴 0.0% 物理 VETO 熔斷 / 全線封島")

        if "無" not in dispatch.get("berthing_pier", ""):
            dispatch["berthing_pier"] = "無 (雙岸失效，禁止靠泊)"
            is_repaired = True
            print("🛠️ [掃兵對齊] 自動修復登島碼頭為: 無 (雙岸失效，禁止靠泊)")

        if "無" not in dispatch.get("evacuation_pier", ""):
            dispatch["evacuation_pier"] = "無 (雙岸失效，直航返航烏石港)"
            is_repaired = True
            print("🛠️ [掃兵對齊] 自動修復撤離碼頭為: 無 (雙岸失效，直航返航烏石港)")

        if "熔斷" not in dispatch.get("tactical_summary", ""):
            dispatch["tactical_summary"] = "🔴 第一位階 Hard VETO 剛性熔斷，全天禁止登島與靠泊"
            is_repaired = True
            print("🛠️ [掃兵對齊] 自動修復戰術總結為: 🔴 第一位階 Hard VETO 剛性熔斷")

    if is_repaired:
        data["physics_metrics"] = physics
        data["guerrilla_dispatch"] = dispatch
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
