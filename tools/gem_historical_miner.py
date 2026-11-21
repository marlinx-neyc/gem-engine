import os
import re
import json
import math
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

CST = timezone(timedelta(hours=8))

class GemHistoricalDataMiner:
    def __init__(
        self,
        db_path: str = "data/calibrated_intel_db.json",
        track_db_path: str = "data/wufu_track.json",
        cwa_api_key: str = None
    ):
        self.db_path = db_path
        self.track_db_path = track_db_path
        self.cwa_api_key = (cwa_api_key or os.environ.get("CWA_API_KEY") or "").strip()
        self.lat = 24.8425
        self.lon = 121.9510
        self.lookback_years = 10

    @staticmethod
    def _compute_historical_qimen_vector(dt_cst: datetime, hs_n: float, tp: float, weff: float, p3h: float, south_closed: int, wufu_in_port: int) -> Tuple[Dict[str, float], str]:
        # 針對近十年 (2016-2026) 任一歷史時間點精確反推奇門天地人神四盤張量
        if dt_cst.tzinfo is None:
            dt_cst = dt_cst.replace(tzinfo=CST)
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
        spring_tide_factor = 0.5 * (1.0 + math.cos(2.0 * math.radians(elongation)))

        solar_terms = [
            "春分", "清明", "穀雨", "立夏", "小滿", "芒種",
            "夏至", "小暑", "大暑", "立秋", "處暑", "白露",
            "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
            "冬至", "小寒", "大寒", "立春", "雨水", "驚蟄"
        ]
        term_name = solar_terms[int(sun_lon // 15.0) % 24]
        yuan_name = ["上元", "中元", "下元"][int((sun_lon % 15.0) // 5.0)]
        dun_type = "陰遁" if (90.0 <= sun_lon < 270.0) else "陽遁"

        is_monsoon = (195.0 <= sun_lon <= 345.0)
        q_heaven = round(min(1.0, 0.55 * spring_tide_factor + (0.35 if is_monsoon else 0.10)), 3)

        if south_closed and hs_n > 0.95:
            q_earth = 0.15
        elif south_closed:
            q_earth = 0.55
        else:
            q_earth = 0.88

        if (south_closed and hs_n > 0.95) or hs_n > 1.13 or weff > 10.17:
            q_human, gate_tag = 0.12, "死門/驚門"
        elif tp >= 12.0 or wufu_in_port == 1:
            q_human, gate_tag = 0.35, "傷門/杜門"
        else:
            q_human, gate_tag = 0.92, "開門"

        if p3h <= -1.4:
            q_deity, deity_tag = 0.88, "白虎"
        elif tp >= 12.0:
            q_deity, deity_tag = 0.85, "騰蛇"
        elif wufu_in_port == 1:
            q_deity, deity_tag = 0.78, "玄武"
        else:
            q_deity, deity_tag = 0.15, "值符"

        q_vec = {
            "q_heaven_tide": q_heaven,
            "q_earth_berth": q_earth,
            "q_human_gate": q_human,
            "q_deity_anomaly": q_deity
        }
        summary = f"{dun_type}·{term_name}{yuan_name}｜{gate_tag}｜{deity_tag}"
        return q_vec, summary

    def _seed_decade_baseline_cases(self) -> List[Dict[str, Any]]:
        # 涵蓋 2016–2026 近十年最具代表性之「例行性封島」、「例外封島」與「灰色地帶開島」基準樣本
        raw_decade_seeds = [
            ("DECADE_2016_0708", "2016-07-08 07:30", "ROUTINE_CLOSURE", "2016尼伯特強颱封島（巨浪蓋頂＋死門白虎）", 3.80, 3.80, 14.5, 18.5, -3.2, 1.15, 3.0, 0, 1, 1, 1.15),
            ("DECADE_2017_1021", "2017-10-21 08:00", "EXCEPTION_CLOSURE", "2017蘭恩颱風外圍長浪例外封島（無陸警但湧浪超限）", 1.75, 1.75, 13.8, 8.2, -1.3, 0.95, 1.4, 0, 1, 1, 1.20),
            ("DECADE_2018_0510", "2018-05-10 08:30", "GRAY_ZONE_OPEN", "2018立夏微湧浪開島（雙岸可用＋值符開門）", 0.78, 0.69, 8.4, 4.1, 0.1, 0.90, 0.0, 0, 0, 0, 1.10),
            ("DECADE_2019_0809", "2019-08-09 07:30", "ROUTINE_CLOSURE", "2019利奇馬強颱封島（巨浪狂風＋死門白虎）", 4.10, 4.10, 15.0, 20.2, -3.8, 1.25, 3.2, 0, 1, 1, 1.15),
            ("DECADE_2020_1106", "2020-11-06 09:00", "EXCEPTION_CLOSURE", "2020閃電颱風外圍長湧浪例外封島（Tp=13.2s）", 1.60, 1.60, 13.2, 7.8, -1.4, 0.88, 1.1, 0, 1, 1, 1.20),
            ("DECADE_2021_0912", "2021-09-12 07:30", "ROUTINE_CLOSURE", "2021璨樹強颱封島（巨浪越浪＋死門白虎）", 3.65, 3.65, 14.2, 17.8, -3.0, 1.10, 2.8, 0, 1, 1, 1.15),
            ("DECADE_2022_1016", "2022-10-16 08:00", "ROUTINE_CLOSURE", "2022尼莎颱風共伴豪雨巨浪封島", 2.95, 2.95, 12.8, 15.4, -2.1, 1.05, 2.5, 0, 1, 1, 1.15),
            ("DECADE_2023_0903", "2023-09-03 07:30", "ROUTINE_CLOSURE", "2023海葵颱風封島（東岸直撲＋死門白虎）", 3.40, 3.40, 13.9, 16.5, -2.8, 1.12, 2.7, 0, 1, 1, 1.15),
            ("DECADE_2024_1031", "2024-10-31 07:30", "ROUTINE_CLOSURE", "2024康芮強颱封島（薔琵/康芮南岸災損前兆）", 4.30, 4.30, 15.4, 21.0, -4.1, 1.30, 3.5, 1, 1, 1, 1.20),
            ("DECADE_2025_0415", "2025-04-15 08:30", "GRAY_ZONE_OPEN", "2025清明穀雨交界開島（南岸封閉但北岸波低穩態）", 0.74, 0.65, 7.8, 3.6, 0.3, 0.92, 0.0, 1, 0, 0, 1.15),
            ("SEED_ROUTINE_01", "2026-11-05 07:30", "ROUTINE_CLOSURE", "2026例行性封島（霜降末東北季風巨浪＋死門白虎）", 2.35, 2.35, 12.1, 12.8, -1.2, 0.62, 2.4, 1, 1, 1, 1.15),
            ("SEED_EXCEPTION_01", "2026-11-15 11:17", "EXCEPTION_CLOSURE", "2026例外封島（立冬中元盤中長湧浪湧升＋傷門騰蛇）", 1.55, 1.55, 12.6, 7.5, -1.5, 0.85, 1.2, 1, 1, 1, 1.25),
            ("SEED_EXCEPTION_02", "2026-11-21 09:00", "EXCEPTION_CLOSURE", "2026例外封島（立冬下元鋒面低壓＋離宮災損＋驚門玄武）", 1.14, 1.01, 6.0, 2.5, -1.6, 1.20, 0.0, 1, 1, 1, 1.35),
            ("SEED_GRAY_OPEN_01", "2026-11-06 07:30", "GRAY_ZONE_OPEN", "2026灰色地帶開島（微浪低風＋開門值符駐島戒護）", 0.82, 0.72, 8.2, 3.5, 0.2, 1.05, 0.0, 1, 0, 0, 1.15),
            ("SEED_NORMAL_OPEN_01", "2026-11-10 08:00", "GRAY_ZONE_OPEN", "2026常態開島（雙岸穩態＋五福號北岸戒護）", 0.65, 0.57, 7.4, 3.0, 0.4, 0.95, 0.0, 0, 0, 0, 1.10)
        ]

        out = []
        for cid, t_str, cat, lbl, hs, hs_n, tp, weff, p3h, tide, cv, s_closed, w_port, veto, wt in raw_decade_seeds:
            dt_obj = datetime.strptime(t_str, "%Y-%m-%d %H:%M").replace(tzinfo=CST)
            q_vec, q_sum = self._compute_historical_qimen_vector(dt_obj, hs_n, tp, weff, p3h, s_closed, w_port)
            out.append({
                "case_id": cid, "time": t_str, "year": dt_obj.year, "category": cat, "label": lbl,
                "hs": hs, "hs_pier_north": hs_n, "tp": tp, "weff": weff, "pressure_3h": p3h,
                "tide": tide, "cv_rate": cv, "south_closed": s_closed, "wufu_in_port": w_port,
                **q_vec, "qimen_summary": q_sum, "veto": veto, "weight": wt, "action": lbl
            })
        return out

    @staticmethod
    def _default_key_values() -> Dict[str, Any]:
        return {
            "hs_pier_north_crit": 0.95,
            "hs_pier_south_crit": 1.13,
            "tp_swell_crit": 12.0,
            "weff_north_crit": 8.50,
            "weff_south_crit": 10.17,
            "pressure_3h_crit": -1.40,
            "cv_overtop_crit": 0.10,
            "rl_decisive_match_pct": 85.0
        }

    @staticmethod
    def _default_11d_scales() -> Dict[str, List[float]]:
        return {
            "hs": [0.45, 0.18],
            "tp": [2.50, 0.12],
            "weff": [3.00, 0.10],
            "pressure_3h": [1.00, 0.10],
            "tide": [0.45, 0.05],
            "south_closed": [0.50, 0.10],
            "wufu_in_port": [0.50, 0.10],
            "q_heaven_tide": [0.35, 0.06],
            "q_earth_berth": [0.35, 0.07],
            "q_human_gate": [0.35, 0.06],
            "q_deity_anomaly": [0.35, 0.06]
        }

    def generate_calibrated_intel_db(self) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        existing_cases = []
        existing_kv = self._default_key_values()
        existing_scales = self._default_11d_scales()
        existing_plan = {}

        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    old_db = json.load(f)
                    existing_cases = old_db.get("historical_cases", [])
                    existing_kv.update(old_db.get("learned_key_values", {}))
                    existing_scales.update(old_db.get("learned_feature_scales", {}))
                    existing_plan = old_db.get("training_plan_report", {})
            except Exception:
                pass

        by_id = {c["case_id"]: c for c in self._seed_decade_baseline_cases() if "case_id" in c}
        for c in existing_cases:
            cid = c.get("case_id")
            if cid:
                by_id[cid] = c

        intel_db = {
            "metadata": {
                "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST"),
                "spec": "GEM-ENG-SPEC-2026-V66.5-10YR-RL-V112",
                "horizon": "2016–2026 (近十年跨尺度樣本庫)",
                "total_cases": len(by_id)
            },
            "learned_key_values": existing_kv,
            "learned_feature_scales": existing_scales,
            "training_plan_report": existing_plan,
            "historical_cases": list(by_id.values())
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(intel_db, f, ensure_ascii=False, indent=2)
        return intel_db

    def _mine_10year_official_closures(self, now_cst: datetime) -> List[Dict[str, Any]]:
        # 階段一：回溯挖掘近十年 (2016–2026) 逐年官方封島新聞公告
        mined_dates = {}
        start_year = now_cst.year - self.lookback_years
        for yr in range(start_year, now_cst.year + 1):
            q = f"%E9%BE%9C%E5%B1%B1%E5%B3%B6+%E5%B0%81%E5%B3%B6+after:{yr}-01-01+before:{yr+1}-01-01"
            rss_url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            try:
                resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    for item in root.findall(".//item")[:5]:
                        title = (item.findtext("title") or "").strip()
                        pub_raw = (item.findtext("pubDate") or "").strip()
                        if "龜山島" in title and re.search(r"(封島|暫停開放|不開放登島|預警性封島)", title):
                            pub_dt = None
                            if pub_raw:
                                try:
                                    pub_dt = parsedate_to_datetime(pub_raw).astimezone(CST)
                                except Exception:
                                    pass
                            if pub_dt and start_year <= pub_dt.year <= now_cst.year:
                                d_str = pub_dt.strftime("%Y-%m-%d")
                                # 排除每年 12月~2月 冬季例行性學術封島休養期，專注海象封島
                                if pub_dt.month not in [12, 1, 2]:
                                    mined_dates[d_str] = {
                                        "date": d_str,
                                        "year": pub_dt.year,
                                        "title": title[:64],
                                        "source": f"google_news_{yr}_rss"
                                    }
            except Exception:
                continue
        return list(mined_dates.values())

    @staticmethod
    def _estimate_smb_wave_from_era5_wind(w_spd: float, wind_dir: float) -> Tuple[float, float]:
        # 針對 2016–2020 Marine API 尚未涵蓋之沿岸網格，以 ERA5 10m 風場透過 SMB 深水波浪成長方程反演 Hs 與 Tp
        d_theta = min(180.0, abs(((wind_dir - 45.0 + 180.0) % 360.0) - 180.0))
        fetch_km = 120.0 if d_theta <= 65.0 else 30.0
        g = 9.81
        u = max(0.5, w_spd)
        gF_u2 = (g * fetch_km * 1000.0) / (u ** 2)
        hs = 0.283 * math.tanh(0.0125 * (gF_u2 ** 0.42)) * (u ** 2) / g
        tp = 7.54 * math.tanh(0.077 * (gF_u2 ** 0.25)) * u / g
        return round(max(0.35, hs), 2), round(max(5.0, min(16.0, tp)), 1)

    def _fetch_archive_wx_for_date(self, date_str: str) -> Optional[Dict[str, float]]:
        # 階段二：核查 ERA5 歷史再分析水文氣象 (2016-2026)
        try:
            w_url = (
                f"https://archive-api.open-meteo.com/v1/archive?latitude={self.lat}&longitude={self.lon}"
                f"&hourly=wind_speed_10m,wind_direction_10m,surface_pressure&wind_speed_unit=ms"
                f"&start_date={date_str}&end_date={date_str}&timezone=Asia%2FTaipei"
            )
            wr = requests.get(w_url, timeout=5)
            if wr.status_code != 200:
                return None
            wh = wr.json().get("hourly", {})
            ws_arr = [float(x) for x in (wh.get("wind_speed_10m") or [])[7:16] if x is not None]
            wd_arr = [float(x) for x in (wh.get("wind_direction_10m") or [])[7:16] if x is not None]
            pr_arr = [float(x) for x in (wh.get("surface_pressure") or []) if x is not None]
            if not ws_arr:
                return None

            w_peak = max(ws_arr)
            w_dir = wd_arr[ws_arr.index(w_peak)] if wd_arr else 45.0
            d_theta = min(180.0, abs(((w_dir - 45.0 + 180.0) % 360.0) - 180.0))
            kw = 0.78 if d_theta < 35.0 else (0.88 if d_theta < 45.0 else 1.00)
            weff = round(w_peak * abs(math.cos(math.radians(d_theta))) * kw, 2)
            p3h = round(pr_arr[11] - pr_arr[8], 1) if len(pr_arr) > 11 else -0.5

            hs_peak, tp_peak = None, None
            m_url = (
                f"https://marine-api.open-meteo.com/v1/marine?latitude={self.lat}&longitude={self.lon}"
                f"&hourly=wave_height,swell_wave_period,wave_period&start_date={date_str}&end_date={date_str}&timezone=Asia%2FTaipei"
            )
            mr = requests.get(m_url, timeout=4)
            if mr.status_code == 200:
                mh = mr.json().get("hourly", {})
                hs_arr = [float(x) for x in (mh.get("wave_height") or [])[7:16] if x is not None]
                tp_raw = mh.get("swell_wave_period") or mh.get("wave_period") or []
                tp_arr = [float(x) for x in tp_raw[7:16] if x is not None]
                if hs_arr:
                    hs_peak = max(hs_arr)
                    tp_peak = max(tp_arr) if tp_arr else 8.5

            if hs_peak is None:
                hs_peak, tp_peak = self._estimate_smb_wave_from_era5_wind(w_peak, w_dir)

            kd_n = 1.00 if tp_peak >= 12.0 else 0.883
            return {
                "hs": round(hs_peak, 2),
                "hs_pier_north": round(hs_peak * kd_n, 2),
                "tp": round(tp_peak, 1),
                "weff": weff,
                "pressure_3h": p3h
            }
        except Exception:
            pass
        return None

    def _summarize_tdx_vessel_patterns(self) -> Dict[str, Any]:
        if not os.path.exists(self.track_db_path):
            return {"total_points": 0, "docked_ratio": 0.0, "retreat_events": 0, "in_port_ratio": 1.0}
        try:
            with open(self.track_db_path, "r", encoding="utf-8") as f:
                pts = json.load(f)
            if not pts:
                return {"total_points": 0, "docked_ratio": 0.0, "retreat_events": 0, "in_port_ratio": 1.0}
            docked = sum(1 for p in pts if "北岸" in str(p.get("tag", "")) or "南岸" in str(p.get("tag", "")))
            in_port = sum(1 for p in pts if "母港" in str(p.get("tag", "")) or "滯港" in str(p.get("tag", "")))
            retreats = sum(1 for p in pts if "返航" in str(p.get("tag", "")))
            return {
                "total_points": len(pts),
                "docked_ratio": round(docked / len(pts), 2),
                "in_port_ratio": round(in_port / len(pts), 2),
                "retreat_events": retreats
            }
        except Exception:
            return {"total_points": 0, "docked_ratio": 0.0, "retreat_events": 0, "in_port_ratio": 1.0}

    @staticmethod
    def _discover_youden_threshold(
        cases: List[Dict[str, Any]], key: str, default_val: float,
        low_b: float, high_b: float, step: float, higher_is_veto: bool = True
    ) -> Tuple[float, float]:
        pos = [c for c in cases if int(c.get("veto", 0)) == 1 and key in c]
        neg = [c for c in cases if int(c.get("veto", 0)) == 0 and key in c]
        if not pos or not neg:
            return default_val, 0.0
        best_th, best_score = default_val, -9.0
        th = low_b
        while th <= high_b + 1e-9:
            if higher_is_veto:
                tpr = sum(c.get("weight", 1.0) for c in pos if float(c[key]) >= th) / sum(c.get("weight", 1.0) for c in pos)
                tnr = sum(c.get("weight", 1.0) for c in neg if float(c[key]) < th) / sum(c.get("weight", 1.0) for c in neg)
            else:
                tpr = sum(c.get("weight", 1.0) for c in pos if float(c[key]) <= th) / sum(c.get("weight", 1.0) for c in pos)
                tnr = sum(c.get("weight", 1.0) for c in neg if float(c[key]) > th) / sum(c.get("weight", 1.0) for c in neg)
            j_stat = tpr + tnr - 1.0
            reg_score = j_stat - 0.03 * abs(th - default_val)
            if reg_score > best_score:
                best_score = reg_score
                best_th = round(th, 2)
            th += step
        return best_th, round(max(0.0, best_score), 3)

    def _optimize_11d_rl_weights(self, cases: List[Dict[str, Any]]) -> Tuple[Dict[str, List[float]], float]:
        base = self._default_11d_scales()
        pos = [c for c in cases if int(c.get("veto", 0)) == 1]
        neg = [c for c in cases if int(c.get("veto", 0)) == 0]
        if not pos or not neg:
            return base, 85.0

        fisher = {}
        for feat, (scale, base_w) in base.items():
            m_p = sum(float(c.get(feat, 0.0)) for c in pos) / len(pos)
            m_n = sum(float(c.get(feat, 0.0)) for c in neg) / len(neg)
            v_p = sum((float(c.get(feat, 0.0)) - m_p) ** 2 for c in pos) / max(1, len(pos))
            v_n = sum((float(c.get(feat, 0.0)) - m_n) ** 2 for c in neg) / max(1, len(neg))
            sep = ((m_p - m_n) ** 2) / (v_p + v_n + (0.25 * scale) ** 2)
            fisher[feat] = base_w * (1.0 + 0.45 * min(3.0, sep))

        tot_w = sum(fisher.values())
        learned = {}
        for feat, (scale, _) in base.items():
            learned[feat] = [round(scale * 1.15, 3), round(fisher[feat] / tot_w, 4)]

        def sim_pct(c1, c2):
            sq, tw = 0.0, 0.0
            for f, (sc, w) in learned.items():
                d = (float(c1.get(f, 0.0)) - float(c2.get(f, 0.0))) / sc
                sq += w * (d ** 2)
                tw += w
            nd = math.sqrt(sq / max(1e-6, tw))
            boost = min(1.06, max(0.92, float(c2.get("weight", 1.0)) ** 0.25))
            return min(99.5, math.exp(-0.55 * (nd ** 2)) * boost * 100.0)

        hits = 0
        for i, c in enumerate(cases):
            best_s, best_v = -1.0, c.get("veto", 0)
            for j, other in enumerate(cases):
                if i == j:
                    continue
                s = sim_pct(c, other)
                if s > best_s:
                    best_s, best_v = s, other.get("veto", 0)
            if best_v == c.get("veto", 0):
                hits += 1
        loocv_acc = round((hits / max(1, len(cases))) * 100.0, 1)
        return learned, loocv_acc

    def run_autonomous_rl_training_cycle(self, force_deep_mine: bool = False) -> Dict[str, Any]:
        # 執行近十年 (2016–2026) 跨尺度四源自主強化學習訓練計畫
        db = self.generate_calibrated_intel_db()
        cases = db.get("historical_cases", [])
        now_cst = datetime.now(CST)
        last_trained = db.get("training_plan_report", {}).get("last_deep_trained_date", "")
        today_str = now_cst.strftime("%Y-%m-%d")
        start_year = now_cst.year - self.lookback_years

        new_mined_count = 0
        if force_deep_mine or (now_cst.hour >= 18 and last_trained != today_str):
            mined_closures = self._mine_10year_official_closures(now_cst)
            existing_ids = {c.get("case_id") for c in cases}
            per_year_counter = {}
            for item in mined_closures:
                yr = item["year"]
                if per_year_counter.get(yr, 0) >= 2:
                    continue
                d_str = item["date"]
                cid = f"MINED_{d_str.replace('-', '')}"
                if cid in existing_ids:
                    continue
                wx = self._fetch_archive_wx_for_date(d_str)
                if wx:
                    per_year_counter[yr] = per_year_counter.get(yr, 0) + 1
                    is_ex = (wx["hs"] <= 1.65 and wx["weff"] <= 8.5)
                    s_closed = 1 if yr >= 2024 else 0
                    dt_obj = datetime.strptime(f"{d_str} 09:00", "%Y-%m-%d %H:%M").replace(tzinfo=CST)
                    q_vec, q_sum = self._compute_historical_qimen_vector(
                        dt_obj, wx["hs_pier_north"], wx["tp"], wx["weff"], wx["pressure_3h"], s_closed, 1
                    )
                    cases.append({
                        "case_id": cid,
                        "time": f"{d_str} 09:00",
                        "year": yr,
                        "category": "EXCEPTION_CLOSURE" if is_ex else "ROUTINE_CLOSURE",
                        "label": f"{yr}{'例外封島' if is_ex else '例行封島'}（{item['title'][:22]}）",
                        "hs": wx["hs"],
                        "hs_pier_north": wx["hs_pier_north"],
                        "tp": wx["tp"],
                        "weff": wx["weff"],
                        "pressure_3h": wx["pressure_3h"],
                        "tide": 0.95,
                        "cv_rate": round(max(0.0, (wx["hs"] - 1.25) * 1.5), 2),
                        "south_closed": s_closed,
                        "wufu_in_port": 1,
                        **q_vec,
                        "qimen_summary": q_sum,
                        "veto": 1,
                        "weight": 1.20,
                        "action": item["title"]
                    })
                    new_mined_count += 1

        tdx_stats = self._summarize_tdx_vessel_patterns()

        hs_n_crit, j_hs = self._discover_youden_threshold(cases, "hs_pier_north", 0.95, 0.85, 1.05, 0.02, True)
        tp_crit, j_tp = self._discover_youden_threshold(cases, "tp", 12.0, 11.2, 12.8, 0.1, True)
        p3h_crit, j_p3h = self._discover_youden_threshold(cases, "pressure_3h", -1.40, -1.80, -1.00, 0.1, False)
        weff_crit, j_weff = self._discover_youden_threshold(cases, "weff", 8.50, 7.50, 9.50, 0.2, True)

        learned_kv = {
            "hs_pier_north_crit": hs_n_crit,
            "hs_pier_south_crit": 1.13,
            "tp_swell_crit": tp_crit,
            "weff_north_crit": weff_crit,
            "weff_south_crit": 10.17,
            "pressure_3h_crit": p3h_crit,
            "cv_overtop_crit": 0.10,
            "rl_decisive_match_pct": 85.0
        }

        learned_scales, loocv_acc = self._optimize_11d_rl_weights(cases)

        years_covered = sorted({int(c.get("year") or str(c.get("time", "2026"))[:4]) for c in cases if str(c.get("time", ""))[:4].isdigit()})
        routine_cnt = sum(1 for c in cases if c.get("category") == "ROUTINE_CLOSURE")
        exc_cnt = sum(1 for c in cases if c.get("category") == "EXCEPTION_CLOSURE")
        open_cnt = sum(1 for c in cases if c.get("category") == "GRAY_ZONE_OPEN")

        plan_report = {
            "last_trained_at": now_cst.strftime("%Y-%m-%d %H:%M:%S CST"),
            "last_deep_trained_date": today_str if (force_deep_mine or now_cst.hour >= 18) else last_trained,
            "time_horizon_span": f"{start_year}–{now_cst.year} (近十年跨尺度樣本庫)",
            "years_covered": years_covered,
            "schedule_policy": "即時線上增量學習 ＋ 每日 18:00 CST 近十年 (2016-2026) 四源深度回溯訓練",
            "total_training_samples": len(cases),
            "category_breakdown": {"routine_closure": routine_cnt, "exception_closure": exc_cnt, "gray_zone_open": open_cnt},
            "new_mined_official_cases": new_mined_count,
            "tdx_behavior_summary": tdx_stats,
            "loocv_accuracy_pct": loocv_acc,
            "key_value_youden_j": {
                "hs_pier_north_crit": f"{hs_n_crit}m (J={j_hs})",
                "tp_swell_crit": f"{tp_crit}s (J={j_tp})",
                "pressure_3h_crit": f"{p3h_crit}hPa/3h (J={j_p3h})",
                "weff_north_crit": f"{weff_crit}m/s (J={j_weff})"
            }
        }

        db["historical_cases"] = cases
        db["learned_key_values"] = learned_kv
        db["learned_feature_scales"] = learned_scales
        db["training_plan_report"] = plan_report
        db["metadata"]["updated_at"] = now_cst.strftime("%Y-%m-%d %H:%M:%S CST")
        db["metadata"]["total_cases"] = len(cases)

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        return {
            "learned_key_values": learned_kv,
            "learned_feature_scales": learned_scales,
            "training_plan_report": plan_report
        }

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
        hs_n = float(physics_metrics.get("hs_pier_north", hs))
        tp = float(physics_metrics.get("tp", telemetry.get("tp", 8.0)))
        weff = float(physics_metrics.get("weff", 4.0))
        p3h = float(physics_metrics.get("pressure_3h", telemetry.get("pressure_3h", 0.0)))
        tide = float(physics_metrics.get("tide", telemetry.get("tide", 0.9)))
        cv_rate = float(physics_metrics.get("cv_rate", telemetry.get("cctv_cv_rate", 0.0)))
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
            "year": now_cst.year,
            "category": cat,
            "label": cat_name,
            "hs": round(hs, 2),
            "hs_pier_north": round(hs_n, 2),
            "tp": round(tp, 1),
            "weff": round(weff, 2),
            "pressure_3h": round(p3h, 2),
            "tide": round(tide, 2),
            "cv_rate": round(cv_rate, 2),
            "south_closed": south_closed,
            "wufu_in_port": wufu_in_port,
            "q_heaven_tide": float(qv.get("q_heaven_tide", 0.5)),
            "q_earth_berth": float(qv.get("q_earth_berth", 0.5)),
            "q_human_gate": float(qv.get("q_human_gate", 0.5)),
            "q_deity_anomaly": float(qv.get("q_deity_anomaly", 0.5)),
            "qimen_summary": qimen_matrix.get("qimen_summary", ""),
            "veto": int(final_veto),
            "weight": 1.35 if is_manual_or_official else 1.15,
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

        seeds = [c for c in cases if str(c.get("case_id", "")).startswith(("SEED_", "DECADE_"))]
        learned = [c for c in cases if not str(c.get("case_id", "")).startswith(("SEED_", "DECADE_"))][-120:]
        db["historical_cases"] = seeds + learned
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        self.run_autonomous_rl_training_cycle(force_deep_mine=False)
        return new_entry
