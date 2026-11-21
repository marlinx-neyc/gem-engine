import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

CST = timezone(timedelta(hours=8))

class GemHistoricalDataMiner:
    def __init__(self, db_path: str = "data/calibrated_intel_db.json"):
        self.db_path = db_path

    def _seed_baseline_cases(self) -> List[Dict[str, Any]]:
        return [
            {
                "case_id": "SEED_ROUTINE_01",
                "time": "2026-11-05 07:30",
                "category": "ROUTINE_CLOSURE",
                "label": "例行性封島（東北季風巨浪蓋頂）",
                "hs": 2.35, "tp": 12.1, "weff": 12.8, "pressure_3h": -1.2,
                "tide": 0.62, "south_closed": 1, "wufu_in_port": 1,
                "veto": 1, "weight": 1.0,
                "action": "🔴 浪潮蓋頂剛性封島"
            },
            {
                "case_id": "SEED_EXCEPTION_01",
                "time": "2026-11-15 11:17",
                "category": "EXCEPTION_CLOSURE",
                "label": "例外封島（盤中長湧浪湧升／外海未達巨浪但碼頭湧浪過大）",
                "hs": 1.55, "tp": 12.6, "weff": 7.5, "pressure_3h": -1.5,
                "tide": 0.85, "south_closed": 1, "wufu_in_port": 1,
                "veto": 1, "weight": 1.15,
                "action": "🔴 盤中長湧浪湧升，五福號返航執行臨時封島"
            },
            {
                "case_id": "SEED_EXCEPTION_02",
                "time": "2026-11-21 09:00",
                "category": "EXCEPTION_CLOSURE",
                "label": "例外封島（鋒面低壓過境＋南岸災損封閉＋北岸波高壓線超標）",
                "hs": 1.14, "tp": 6.0, "weff": 2.5, "pressure_3h": -1.6,
                "tide": 1.20, "south_closed": 1, "wufu_in_port": 1,
                "veto": 1, "weight": 1.25,
                "action": "🔴 現場視訊碼頭浪潮過大且南岸封閉，宣布例外封島"
            },
            {
                "case_id": "SEED_GRAY_OPEN_01",
                "time": "2026-11-06 07:30",
                "category": "GRAY_ZONE_OPEN",
                "label": "灰色地帶開島（微浪低風＋五福號駐島戒護）",
                "hs": 0.82, "tp": 8.2, "weff": 3.5, "pressure_3h": 0.2,
                "tide": 1.05, "south_closed": 1, "wufu_in_port": 0,
                "veto": 0, "weight": 1.0,
                "action": "🟢 北岸單泊位安全開窗（五福號駐島）"
            }
        ]

    def generate_calibrated_intel_db(self) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        existing_cases = []
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    old_db = json.load(f)
                    existing_cases = old_db.get("historical_cases", [])
            except Exception:
                existing_cases = []

        by_id = {c["case_id"]: c for c in self._seed_baseline_cases() if "case_id" in c}
        for c in existing_cases:
            cid = c.get("case_id")
            if cid:
                by_id[cid] = c

        intel_db = {
            "metadata": {
                "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
                "spec": "GEM-ENG-SPEC-2026-V66.5-RL-INTEL",
                "total_cases": len(by_id)
            },
            "historical_cases": list(by_id.values())
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(intel_db, f, ensure_ascii=False, indent=2)
        return intel_db

    def record_rl_feedback(
        self,
        telemetry: Dict[str, Any],
        physics_metrics: Dict[str, Any],
        final_veto: int,
        reason_label: str,
        is_manual_or_official: bool = False
    ) -> Dict[str, Any]:
        db = self.generate_calibrated_intel_db()
        cases = db.get("historical_cases", [])
        now_cst = datetime.now(CST)
        today_key = now_cst.strftime("RL_%Y%m%d")

        hs = float(physics_metrics.get("hs", telemetry.get("hs", 1.0)))
        tp = float(physics_metrics.get("tp", telemetry.get("tp", 8.0)))
        weff = float(physics_metrics.get("weff", 4.0))
        p3h = float(physics_metrics.get("pressure_3h", telemetry.get("pressure_3h", 0.0)))
        tide = float(physics_metrics.get("tide", telemetry.get("tide", 0.9)))
        south_closed = 1 if telemetry.get("official_announcement", {}).get("south_pier_closed_damage", True) else 0
        wufu_in_port = 1 if final_veto == 1 else 0

        if final_veto == 1:
            if hs <= 1.65 and weff <= 8.5:
                cat = "EXCEPTION_CLOSURE"
                cat_name = f"例外封島（{reason_label[:28]}）"
            else:
                cat = "ROUTINE_CLOSURE"
                cat_name = f"例行性封島（{reason_label[:28]}）"
        else:
            cat = "GRAY_ZONE_OPEN"
            cat_name = f"實證開島（{reason_label[:28]}）"

        new_entry = {
            "case_id": today_key,
            "time": now_cst.strftime("%Y-%m-%d %H:%M"),
            "category": cat,
            "label": cat_name,
            "hs": round(hs, 2),
            "tp": round(tp, 1),
            "weff": round(weff, 2),
            "pressure_3h": round(p3h, 2),
            "tide": round(tide, 2),
            "south_closed": south_closed,
            "wufu_in_port": wufu_in_port,
            "veto": int(final_veto),
            "weight": 1.35 if is_manual_or_official else 1.10,
            "action": reason_label
        }

        updated = False
        for idx, c in enumerate(cases):
            if c.get("case_id") == today_key:
                if is_manual_or_official or c.get("weight", 1.0) <= new_entry["weight"]:
                    cases[idx] = new_entry
                updated = True
                break
        if not updated:
            cases.append(new_entry)

        seeds = [c for c in cases if str(c.get("case_id", "")).startswith("SEED_")]
        learned = [c for c in cases if not str(c.get("case_id", "")).startswith("SEED_")][-60:]
        db["historical_cases"] = seeds + learned
        db["metadata"]["updated_at"] = now_cst.strftime("%Y-%m-%d %H:%M:%S CST")
        db["metadata"]["total_cases"] = len(db["historical_cases"])

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        return new_entry
