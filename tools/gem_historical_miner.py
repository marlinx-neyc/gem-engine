import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

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
                "label": "例行性封島（霜降末東北季風巨浪＋死門白虎）",
                "hs": 2.35, "tp": 12.1, "weff": 12.8, "pressure_3h": -1.2,
                "tide": 0.62, "south_closed": 1, "wufu_in_port": 1,
                "q_heaven_tide": 0.85, "q_earth_berth": 0.15, "q_human_gate": 0.10, "q_deity_anomaly": 0.85,
                "qimen_summary": "陰遁·霜降下元｜艮宮受沖｜死門｜白虎",
                "veto": 1, "weight": 1.0,
                "action": "🔴 浪潮蓋頂剛性封島"
            },
            {
                "case_id": "SEED_EXCEPTION_01",
                "time": "2026-11-15 11:17",
                "category": "EXCEPTION_CLOSURE",
                "label": "例外封島（立冬中元盤中長湧浪湧升＋傷門騰蛇）",
                "hs": 1.55, "tp": 12.6, "weff": 7.5, "pressure_3h": -1.5,
                "tide": 0.85, "south_closed": 1, "wufu_in_port": 1,
                "q_heaven_tide": 0.65, "q_earth_berth": 0.25, "q_human_gate": 0.30, "q_deity_anomaly": 0.90,
                "qimen_summary": "陰遁·立冬中元｜艮宮湧浪｜傷門｜騰蛇",
                "veto": 1, "weight": 1.15,
                "action": "🔴 盤中長湧浪湧升，五福號返航執行臨時封島"
            },
            {
                "case_id": "SEED_EXCEPTION_02",
                "time": "2026-11-21 09:00",
                "category": "EXCEPTION_CLOSURE",
                "label": "例外封島（立冬下元鋒面低壓＋離宮災損＋驚門玄武）",
                "hs": 1.14, "tp": 6.0, "weff": 2.5, "pressure_3h": -1.6,
                "tide": 1.20, "south_closed": 1, "wufu_in_port": 1,
                "q_heaven_tide": 0.52, "q_earth_berth": 0.20, "q_human_gate": 0.20, "q_deity_anomaly": 0.88,
                "qimen_summary": "陰遁·立冬下元｜離宮災損艮宮壓線｜驚門｜玄武",
                "veto": 1, "weight": 1.30,
                "action": "🔴 鋒面低壓長湧浪＋南岸災損，宣布例外封島"
            },
            {
                "case_id": "SEED_GRAY_OPEN_01",
                "time": "2026-11-06 07:30",
                "category": "GRAY_ZONE_OPEN",
                "label": "灰色地帶開島（微浪低風＋開門值符駐島戒護）",
                "hs": 0.82, "tp": 8.2, "weff": 3.5, "pressure_3h": 0.2,
                "tide": 1.05, "south_closed": 1, "wufu_in_port": 0,
                "q_heaven_tide": 0.35, "q_earth_berth": 0.78, "q_human_gate": 0.90, "q_deity_anomaly": 0.15,
                "qimen_summary": "陰遁·霜降下元｜坎北平穩｜開門｜值符",
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
                "spec": "GEM-ENG-SPEC-2026-V66.5-QIMEN-RL-V110",
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
        qimen_matrix: Optional[Dict[str, Any]] = None,
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
        qimen_matrix = qimen_matrix or {}
        qv = qimen_matrix.get("qimen_vector", {})

        if final_veto == 1:
            if hs <= 1.65 and weff <= 8.5:
                cat = "EXCEPTION_CLOSURE"
                cat_name = f"例外封島（{reason_label[:26]}）"
            else:
                cat = "ROUTINE_CLOSURE"
                cat_name = f"例行性封島（{reason_label[:26]}）"
        else:
            cat = "GRAY_ZONE_OPEN"
            cat_name = f"實證開島（{reason_label[:26]}）"

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
            "q_heaven_tide": float(qv.get("q_heaven_tide", 0.5)),
            "q_earth_berth": float(qv.get("q_earth_berth", 0.5)),
            "q_human_gate": float(qv.get("q_human_gate", 0.5)),
            "q_deity_anomaly": float(qv.get("q_deity_anomaly", 0.5)),
            "qimen_summary": qimen_matrix.get("qimen_summary", ""),
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
