import os
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

CST = timezone(timedelta(hours=8))

class GemMacroRLOrchestrator:
    DECISIVE_THRESHOLD_PCT = 85.0

    def __init__(self, intel_db_path: str = "data/calibrated_intel_db.json"):
        self.intel_db_path = intel_db_path
        self.feature_scales = {
            "hs": (0.52, 0.18),
            "tp": (3.00, 0.12),
            "weff": (3.50, 0.10),
            "pressure_3h": (1.15, 0.10),
            "tide": (0.60, 0.04),
            "south_closed": (0.60, 0.10),
            "wufu_abnormal_detained": (0.55, 0.11),
            "q_heaven_tide": (0.45, 0.06),
            "q_earth_berth": (0.42, 0.07),
            "q_human_gate": (0.42, 0.06),
            "q_deity_anomaly": (0.42, 0.06),
        }

    def parse_qimen_matrix(
        self,
        dt: datetime = None,
        live_telemetry: Dict[str, Any] = None,
        physics_metrics: Dict[str, Any] = None,
        vessel_res: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        dt_cst = dt or datetime.now(CST)
        if dt_cst.tzinfo is None:
            dt_cst = dt_cst.replace(tzinfo=CST)
        live_telemetry = live_telemetry or {}
        physics_metrics = physics_metrics or {}
        vessel_res = vessel_res or {}
        wufu = vessel_res.get("official_wufu", {})
        ann = live_telemetry.get("official_announcement", {})

        # 一、天盤：日月黃經、二十四節氣、陰陽遁與朔望引潮力係數
        dt_utc = dt_cst.astimezone(timezone.utc)
        y, m = dt_utc.year, dt_utc.month
        d = dt_utc.day + (dt_utc.hour + dt_utc.minute / 60.0) / 24.0
        if m <= 2:
            y -= 1
            m += 12
        A = y // 100
        B = 2 - A + (A // 4)
        jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
        T = (jd - 2451545.0) / 36525.0

        L0 = (280.46646 + 36000.76983 * T) % 360.0
        M = math.radians((357.52911 + 35999.05029 * T) % 360.0)
        C = (1.914602 - 0.004817 * T) * math.sin(M) + 0.019993 * math.sin(2 * M)
        sun_lon = (L0 + C) % 360.0

        Lm = (218.3164477 + 481267.88123421 * T) % 360.0
        Mm = math.radians((134.9633964 + 477198.8675055 * T) % 360.0)
        moon_lon = (Lm + 6.288774 * math.sin(Mm)) % 360.0
        elongation = (moon_lon - sun_lon) % 360.0

        spring_tide_factor = round(0.5 * (1.0 + math.cos(2.0 * math.radians(elongation))), 3)
        lunar_age = round((elongation / 360.0) * 29.530588, 1)

        solar_terms = [
            "春分", "清明", "穀雨", "立夏", "小滿", "芒種",
            "夏至", "小暑", "大暑", "立秋", "處暑", "白露",
            "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
            "冬至", "小寒", "大寒", "立春", "雨水", "驚蟄"
        ]
        term_name = solar_terms[int(sun_lon // 15.0) % 24]
        yuan_name = ["上元", "中元", "下元"][int((sun_lon % 15.0) // 5.0)]
        dun_type = "陰遁" if (90.0 <= sun_lon < 270.0) else "陽遁"

        shichen_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        shichen = shichen_names[((dt_cst.hour + 1) // 2) % 12] + "時"

        is_monsoon_season = (195.0 <= sun_lon <= 345.0)
        q_heaven_tide = round(min(1.0, 0.55 * spring_tide_factor + (0.35 if is_monsoon_season else 0.10)), 3)
        heaven_desc = f"{dun_type}·{term_name}{yuan_name} ({shichen}, 月齡{lunar_age}日, 引潮係數{spring_tide_factor})"

        # 二、地盤：洛書九宮方位與泊位完整度
        south_closed = bool(ann.get("south_pier_closed_damage", True))
        hs_n = float(physics_metrics.get("hs_pier_north", live_telemetry.get("hs", 1.0)))
        hs_s = float(physics_metrics.get("hs_pier_south", 0.8))
        wind_dir = float(live_telemetry.get("wind_dir", 45.0))

        is_gen_attack = (20.0 <= wind_dir <= 75.0)
        if south_closed and hs_n > 0.95:
            q_earth_berth = 0.15
            earth_desc = "離宮(南岸)災損封閉 ＋ 艮宮(東北)沖擊坎宮(北岸超限)，全島無可用泊位"
        elif south_closed:
            q_earth_berth = 0.62
            earth_desc = "離宮(南岸)災損封閉，單靠坎宮(北岸)獨撐"
        elif is_gen_attack and hs_s <= 1.13:
            q_earth_berth = 0.75
            earth_desc = "艮宮(東北)風浪偏強，宜轉進離宮(南岸)背風屏蔽"
        else:
            q_earth_berth = 0.92
            earth_desc = "坎離雙宮泊位完整，地形屏蔽穩固"

        # 三、人盤：八門動態航行時窗張量
        in_hours = (7 * 60 <= dt_cst.hour * 60 + dt_cst.minute <= 16 * 60 + 30)
        tp = float(physics_metrics.get("tp", live_telemetry.get("tp", 8.0)))
        weff = float(physics_metrics.get("weff", 4.0))
        cv_rate = float(physics_metrics.get("cv_rate", live_telemetry.get("cctv_cv_rate", 0.0)))
        pm_risk = bool(live_telemetry.get("pm_forecast", {}).get("afternoon_risk", False))

        if (south_closed and hs_n > 0.95) or (hs_n > 1.13 and hs_s > 1.13) or weff > 10.17:
            gate_name = "死門/驚門 (凶門熔斷)"
            q_human_gate = 0.12
        elif tp >= 12.0 or cv_rate > 0.0 or pm_risk:
            gate_name = "傷門/杜門 (午後湧浪受阻)"
            q_human_gate = 0.35
        elif not in_hours:
            gate_name = "休門 (夜間休整養息)"
            q_human_gate = 0.80
        elif hs_n > 0.85:
            gate_name = "生門 (調撥偏吉)"
            q_human_gate = 0.84
        else:
            gate_name = "開門 (三吉門·暢行)"
            q_human_gate = 0.95

        # 四、神盤：八神非線性相變異常算子
        p3h = float(physics_metrics.get("pressure_3h", live_telemetry.get("pressure_3h", 0.0)))
        http_logs = " ".join(ann.get("scraper_diagnostics", {}).get("http_statuses", []))
        gov_blind = ("necoast-nsa.gov.tw" in http_logs and ":200" not in http_logs)
        bh_rough = bool(live_telemetry.get("blue_highway", {}).get("is_rough_sea", False))

        if p3h <= -1.4 or bh_rough:
            deity_name = "白虎/玄武 (鋒面氣壓驟降/藍色公路大浪)"
            q_deity_anomaly = 0.88
        elif tp >= 12.0:
            deity_name = "騰蛇 (長週期湧浪糾纏突襲)"
            q_deity_anomaly = 0.85
        elif in_hours and gov_blind and not wufu.get("is_docked_island", False):
            deity_name = "玄武 (船班時段官網盲區＋船訊隱匿)"
            q_deity_anomaly = 0.80
        elif hs_n <= 0.88 and weff <= 6.5:
            deity_name = "值符 (八神之首·海象清朗)"
            q_deity_anomaly = 0.15
        else:
            deity_name = "太陰/六合 (常態微幅波動)"
            q_deity_anomaly = 0.25

        w_qimen = round(0.30 * (1.0 - q_heaven_tide) + 0.30 * q_earth_berth + 0.25 * q_human_gate + 0.15 * (1.0 - q_deity_anomaly), 3)
        summary_str = f"{dun_type}·{term_name}{yuan_name}｜{gate_name.split(' ')[0]}｜{deity_name.split(' ')[0]}"

        return {
            "w_qimen": w_qimen,
            "qimen_gate": gate_name,
            "qimen_deity": deity_name,
            "qimen_heaven": heaven_desc,
            "qimen_earth": earth_desc,
            "qimen_summary": summary_str,
            "qimen_vector": {
                "q_heaven_tide": q_heaven_tide,
                "q_earth_berth": q_earth_berth,
                "q_human_gate": q_human_gate,
                "q_deity_anomaly": q_deity_anomaly
            }
        }

    def _load_cases(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.intel_db_path):
            try:
                with open(self.intel_db_path, "r", encoding="utf-8") as f:
                    db = json.load(f)
                    learned_scales = db.get("learned_feature_scales", {})
                    for k, v in learned_scales.items():
                        mapped_k = "wufu_abnormal_detained" if k == "wufu_in_port" else k
                        if mapped_k in self.feature_scales and isinstance(v, (list, tuple)) and len(v) == 2:
                            self.feature_scales[mapped_k] = (max(float(v[0]), self.feature_scales[mapped_k][0]), float(v[1]))
                    return db.get("historical_cases", [])
            except Exception:
                pass
        return []

    def _compute_rq_similarity_pct(self, cur: Dict[str, float], case: Dict[str, Any]) -> float:
        # 比例二次核 (Rational Quadratic Kernel, α=1.5) + RL 溫度校準 (τ=0.72)
        weighted_sq_dist = 0.0
        total_w = 0.0
        for feat, (scale, w) in self.feature_scales.items():
            v1 = float(cur.get(feat, 0.0))
            if feat == "wufu_abnormal_detained" and feat not in case:
                v2 = float(case.get("wufu_in_port", v1))
            else:
                v2 = float(case.get(feat, v1))
            diff = (v1 - v2) / scale
            weighted_sq_dist += w * (diff ** 2)
            total_w += w
        norm_d2 = weighted_sq_dist / max(1e-6, total_w)
        alpha = 1.5
        tau = 0.72
        k_val = (1.0 + (norm_d2 / (2.0 * alpha * tau))) ** (-alpha)
        rl_boost = min(1.04, max(0.96, float(case.get("weight", 1.0)) ** 0.15))
        return round(min(99.2, k_val * rl_boost * 100.0), 1)

    def evaluate_rl_match_with_hysteresis(
        self,
        live_telemetry: Dict[str, Any],
        physics_metrics: Dict[str, Any] = None,
        vessel_res: Dict[str, Any] = None,
        dt: datetime = None
    ) -> Dict[str, Any]:
        dt_cst = dt or datetime.now(CST)
        if dt_cst.tzinfo is None:
            dt_cst = dt_cst.replace(tzinfo=CST)
        physics_metrics = physics_metrics or {}
        vessel_res = vessel_res or {}
        wufu = vessel_res.get("official_wufu", {})
        ann = live_telemetry.get("official_announcement", {})

        in_hours = (7 * 60 <= dt_cst.hour * 60 + dt_cst.minute <= 16 * 60 + 30)
        # 僅在「船班營運時段 (07:00-16:30)」未駐島才視為異常滯港 (1.0)；夜間休整停母港為正常 (0.0)
        wufu_detained = 1.0 if (in_hours and not wufu.get("is_docked_island", False)) else 0.0

        qimen = self.parse_qimen_matrix(
            dt=dt_cst, live_telemetry=live_telemetry, physics_metrics=physics_metrics, vessel_res=vessel_res
        )
        qv = qimen["qimen_vector"]

        cur_vec = {
            "hs": float(physics_metrics.get("hs", live_telemetry.get("hs", 1.0))),
            "tp": float(physics_metrics.get("tp", live_telemetry.get("tp", 8.0))),
            "weff": float(physics_metrics.get("weff", 4.0)),
            "pressure_3h": float(physics_metrics.get("pressure_3h", live_telemetry.get("pressure_3h", 0.0))),
            "tide": float(physics_metrics.get("tide", live_telemetry.get("tide", 0.9))),
            "south_closed": 1.0 if ann.get("south_pier_closed_damage", True) else 0.0,
            "wufu_abnormal_detained": wufu_detained,
            "q_heaven_tide": qv["q_heaven_tide"],
            "q_earth_berth": qv["q_earth_berth"],
            "q_human_gate": qv["q_human_gate"],
            "q_deity_anomaly": qv["q_deity_anomaly"],
        }

        cases = self._load_cases()
        if not cases:
            return {
                "match_score": 0.0, "has_suggestion": False, "rl_veto_triggered": False,
                "matched_category": "NONE", "qimen_matrix": qimen, "suggestion": "智庫初始化中"
            }

        scored = []
        for c in cases:
            sim = self._compute_rq_similarity_pct(cur_vec, c)
            scored.append((sim, c))
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_case = scored[0]
        # 同類 Top-2 原型加權融合平滑（消除單一歷史樣本雜訊）
        same_class_scores = [s for s, c in scored if int(c.get("veto", 0)) == int(best_case.get("veto", 0))]
        if len(same_class_scores) >= 2:
            fused_score = round(min(99.2, 0.78 * same_class_scores[0] + 0.22 * same_class_scores[1] + 1.8), 1)
        else:
            fused_score = best_score

        is_decisive = fused_score >= self.DECISIVE_THRESHOLD_PCT
        matched_veto = int(best_case.get("veto", 0)) == 1
        cat = best_case.get("category", "UNKNOWN")
        cat_label = best_case.get("label", "歷史案例")

        if is_decisive and matched_veto:
            msg = f"🔴 11D奇門RL智庫高置信收斂 ({fused_score}% >= 85%)：【{qimen['qimen_summary']}】吻合【{cat_label}】，灰色地帶坍縮為 VETO！"
        elif is_decisive and not matched_veto:
            msg = f"🟢 11D奇門RL智庫高置信收斂 ({fused_score}% >= 85%)：【{qimen['qimen_summary']}】吻合【{cat_label}】，支援安全開窗作業。"
        else:
            msg = f"🟡 11D奇門RL智庫觀望 ({fused_score}% < 85%)：【{qimen['qimen_summary']}】，最接近【{cat_label}】。"

        return {
            "match_score": fused_score,
            "has_suggestion": True,
            "is_decisive_80": is_decisive,
            "is_decisive_85": is_decisive,
            "rl_veto_triggered": bool(is_decisive and matched_veto),
            "rl_open_triggered": bool(is_decisive and not matched_veto),
            "matched_category": cat,
            "matched_case_id": best_case.get("case_id", ""),
            "matched_label": cat_label,
            "qimen_matrix": qimen,
            "suggestion": msg
        }
