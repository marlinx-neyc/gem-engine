import re
import time
import math
import requests
import numpy as np
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

class GemScoutAgent:
    def __init__(self, cwa_api_key: str = None, fb_page_token: str = None, fb_page_id: str = None):
        self.cwa_api_key = cwa_api_key
        self.fb_page_token = fb_page_token
        self.fb_page_id = fb_page_id
        self.lat = 24.8425
        self.lon = 121.9510
        self.official_urls = [
            "https://www.necoast-nsa.gov.tw/",
            "https://www.necoast-nsa.gov.tw/News.aspx?n=88"
        ]

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)

    def _check_date_relevance(self, text: str, now_cst: datetime, pub_dt: datetime = None) -> dict:
        today_m, today_d = now_cst.month, now_cst.day
        tmr = now_cst + timedelta(days=1)
        tmr_m, tmr_d = tmr.month, tmr.day

        # 若貼文/公告帶有發布時間且已超過 18 小時，除非明確寫出今日日期或「續封」，否則視為歷史過期公告
        if pub_dt is not None:
            age_hours = (now_cst - pub_dt).total_seconds() / 3600.0
            if age_hours > 18.0 and not re.search(rf"({today_m}月{today_d}日|{today_m}/{today_d}|續封)", text):
                return {"valid": False, "is_today": False, "is_tmr": False, "scope": "FULL_DAY", "stale_filtered": True}

        is_today = bool(re.search(rf"(本日封島|今日封島|今天封島|下午封島|封島半天|今\({today_d}\)日|{today_m}月{today_d}日|{today_m}/{today_d})", text))
        is_tmr = bool(re.search(rf"(明日封島|明天封島|續封島|明\({tmr_d}\)日|{tmr_m}月{tmr_d}日|{tmr_m}/{tmr_d})", text))
        scope = "AFTERNOON" if re.search(r"(下午封島|封島半天|午後封島|12:00)", text) else "FULL_DAY"

        has_explicit_date = bool(re.search(r"\d{1,2}月\d{1,2}日", text))
        if has_explicit_date and not is_today and not is_tmr:
            return {"valid": False, "is_today": False, "is_tmr": False, "scope": scope, "stale_filtered": True}
        if not has_explicit_date and not is_today and not is_tmr:
            return {"valid": False, "is_today": False, "is_tmr": False, "scope": scope, "stale_filtered": False}
        return {"valid": True, "is_today": is_today, "is_tmr": is_tmr, "scope": scope, "stale_filtered": False}

    def fetch_facebook_announcement(self) -> dict:
        if not self.fb_page_token or not self.fb_page_id:
            return None
        url = f"https://graph.facebook.com/v18.0/{self.fb_page_id}/published_posts"
        params = {"access_token": self.fb_page_token, "limit": 3, "fields": "message,created_time"}
        now_cst = datetime.now(CST)
        try:
            resp = requests.get(url, params=params, timeout=4)
            if resp.status_code == 200:
                for post in resp.json().get("data", []):
                    msg = post.get("message", "")
                    created_raw = post.get("created_time", "")
                    pub_dt = None
                    if created_raw:
                        try:
                            pub_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).astimezone(CST)
                        except Exception:
                            pub_dt = None
                    if "龜山島" in msg and re.search(r"(封島|暫停開放|不開放登島)", msg):
                        rel = self._check_date_relevance(msg, now_cst, pub_dt=pub_dt)
                        if rel["valid"]:
                            return {
                                "official_veto": 1 if rel["is_today"] else 0,
                                "tomorrow_veto": 1 if rel["is_tmr"] else 0,
                                "scope": rel["scope"],
                                "wave_warning": True,
                                "title": f"【FB 社群公告】{msg[:36]}...",
                                "body": msg,
                                "source": "facebook_api",
                                "published_at": pub_dt.strftime("%Y-%m-%d %H:%M CST") if pub_dt else created_raw
                            }
        except Exception:
            pass
        return None

    def fetch_official_announcement(self, override_announcement: dict = None) -> dict:
        if override_announcement:
            return override_announcement
        fb_res = self.fetch_facebook_announcement()
        if fb_res and (fb_res.get("official_veto") == 1 or fb_res.get("tomorrow_veto") == 1):
            return fb_res

        now = datetime.now(CST)
        current_day = now.day
        tomorrow_day = (now + timedelta(days=1)).day

        default_payload = {
            "official_veto": 0,
            "tomorrow_veto": 0,
            "scope": "FULL_DAY",
            "wave_warning": False,
            "title": "【風管處通告】全島常規開放營運中",
            "body": "東北角暨宜蘭海岸國家風景區管理處：龜山島今日無當日封島通告，依實船軌跡與海象動態開放登島。",
            "published_at": now.strftime("%Y-%m-%d %H:%M CST"),
            "extracted_day": current_day,
            "source": "official_web"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
        buster = int(time.time())
        for base_url in self.official_urls:
            sep = "&" if "?" in base_url else "?"
            url = f"{base_url}{sep}_t={buster}"
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    if HAS_BS4:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        candidates = [el.get_text(" ", strip=True) for el in soup.find_all(["a", "li", "h2", "h3", "div"]) if "龜山島" in el.get_text()]
                    else:
                        clean_txt = re.sub(r"<[^>]+>", "\n", resp.text)
                        candidates = [ln.strip() for ln in clean_txt.splitlines() if "龜山島" in ln]
                    for snippet in candidates:
                        if len(snippet) > 180:
                            continue
                        if re.search(r"(封島|禁止靠泊|浪潮蓋碼頭|暫停開放|不開放登島)", snippet):
                            rel = self._check_date_relevance(snippet, now)
                            if rel["valid"]:
                                target_d = current_day if rel["is_today"] else tomorrow_day
                                scope_txt = "下午封島半天" if rel["scope"] == "AFTERNOON" else "實施封島"
                                default_payload.update({
                                    "official_veto": 1 if rel["is_today"] else 0,
                                    "tomorrow_veto": 1 if rel["is_tmr"] else 0,
                                    "scope": rel["scope"],
                                    "wave_warning": True,
                                    "title": f"【風管處公告】受海浪影響，({target_d})日龜山島{scope_txt}",
                                    "body": snippet,
                                    "extracted_day": target_d
                                })
                                return default_payload
                    break
            except Exception:
                continue
        return default_payload

    def fetch_cwa_buoy_realtime(self) -> dict:
        if not self.cwa_api_key:
            return None
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-B0075-001?Authorization={self.cwa_api_key}&StationID=46708A,46694A,C6U01"
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                locs = resp.json().get("Records", {}).get("SeaSurfaceObs", {}).get("Location", [])
                for loc in locs:
                    obs_list = loc.get("StationObsTimes", {}).get("StationObsTime", [])
                    if not obs_list:
                        continue
                    latest = obs_list[-1].get("WeatherElements", {})
                    wh = latest.get("WaveHeight")
                    wp = latest.get("WavePeriod")
                    if wh not in [None, "None", "-", "-99"] and wp not in [None, "None", "-", "-99"]:
                        return {
                            "hs": float(wh),
                            "tp": float(wp),
                            "station": loc.get("Station", {}).get("StationName", "CWA浮標")
                        }
        except Exception:
            pass
        return None

    def fetch_live_marine_and_weather(self) -> dict:
        marine_url = (
            f"https://marine-api.open-meteo.com/v1/marine?"
            f"latitude={self.lat}&longitude={self.lon}"
            f"&current=wave_height,wave_period,swell_wave_height,swell_wave_period"
            f"&hourly=wave_height,wave_period,swell_wave_period"
            f"&daily=wave_height_max,wave_period_max&forecast_days=7&timezone=Asia%2FTaipei"
        )
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.lat}&longitude={self.lon}"
            f"&current=wind_speed_10m,wind_direction_10m,surface_pressure"
            f"&hourly=surface_pressure,wind_speed_10m&daily=wind_speed_10m_max"
            f"&wind_speed_unit=ms&forecast_days=7&timezone=Asia%2FTaipei"
        )
        res = {
            "hs": 1.15, "tp": 8.5, "w": 5.5, "wind_dir": 45.0,
            "monsoon_angle": 35.0, "pressure": 1014.0, "pressure_3h": -0.5,
            "tide": 0.95, "daily_forecast": [],
            "pm_forecast": {"pm_hs_max": 1.15, "pm_tp_max": 8.5, "hs_slope_3h": 0.0, "afternoon_risk": False, "risk_label": "🟢 午後海象平穩"},
            "data_source": "fallback_baseline"
        }
        try:
            m_resp = requests.get(marine_url, timeout=5)
            w_resp = requests.get(weather_url, timeout=5)
            if m_resp.status_code == 200 and w_resp.status_code == 200:
                m_data = m_resp.json()
                w_data = w_resp.json()
                m_cur = m_data.get("current", {})
                w_cur = w_data.get("current", {})

                hs = float(m_cur.get("wave_height") or 1.15)
                tp = float(m_cur.get("swell_wave_period") or m_cur.get("wave_period") or 8.5)
                src_tag = "open_meteo_live"

                cwa_buoy = self.fetch_cwa_buoy_realtime()
                if cwa_buoy:
                    hs = max(hs, cwa_buoy["hs"])
                    tp = max(tp, cwa_buoy["tp"])
                    src_tag = f"cwa_buoy({cwa_buoy['station']})+open_meteo"

                w_spd = float(w_cur.get("wind_speed_10m") or 5.5)
                w_dir = float(w_cur.get("wind_direction_10m") or 45.0)
                pressure = float(w_cur.get("surface_pressure") or 1014.0)
                delta_theta = min(180.0, abs(((w_dir - 45.0 + 180.0) % 360.0) - 180.0))

                now_cst = datetime.now(CST)
                now_hr = now_cst.hour

                p_3h = 0.0
                hourly_p = w_data.get("hourly", {}).get("surface_pressure", [])
                if len(hourly_p) > now_hr and now_hr >= 3:
                    p_3h = round(float(hourly_p[now_hr]) - float(hourly_p[now_hr - 3]), 1)

                h_hs = m_data.get("hourly", {}).get("wave_height", [])
                h_tp = m_data.get("hourly", {}).get("swell_wave_period") or m_data.get("hourly", {}).get("wave_period") or []
                hs_slope_3h = 0.0
                if len(h_hs) > now_hr + 3 and h_hs[now_hr] is not None and h_hs[now_hr + 3] is not None:
                    hs_slope_3h = round(float(h_hs[now_hr + 3]) - float(h_hs[now_hr]), 2)

                pm_hs_vals = [float(h_hs[i]) for i in range(12, min(18, len(h_hs))) if h_hs[i] is not None]
                pm_tp_vals = [float(h_tp[i]) for i in range(12, min(18, len(h_tp))) if h_tp[i] is not None]
                pm_hs_max = round(max([hs] + pm_hs_vals) if pm_hs_vals else hs, 2)
                pm_tp_max = round(max([tp] + pm_tp_vals) if pm_tp_vals else tp, 1)

                kd_s_pm = 1.00 if pm_tp_max >= 12.0 else 0.72
                pm_hs_south = pm_hs_max * kd_s_pm
                afternoon_risk = bool(
                    (pm_tp_max >= 12.0 and pm_hs_south > 1.13)
                    or (pm_hs_south > 1.13)
                    or (hs_slope_3h >= 0.30 and pm_hs_max >= 1.45)
                )
                risk_label = (
                    f"🟡 午後封島高風險預警 (PM Hs={pm_hs_max}m, Tp={pm_tp_max}s, 斜率{hs_slope_3h:+.2f}m/3h)"
                    if afternoon_risk else
                    f"🟢 午後海象受控 (PM Hs={pm_hs_max}m, Tp={pm_tp_max}s)"
                )

                tide_est = round(0.85 + 0.45 * math.sin(2 * math.pi * (now_cst.hour + now_cst.minute / 60.0) / 12.42), 2)
                m_daily = m_data.get("daily", {})
                w_daily = w_data.get("daily", {})
                dates = m_daily.get("time", [])
                hs_max_list = m_daily.get("wave_height_max", [])
                tp_max_list = m_daily.get("wave_period_max", [])
                w_max_list = w_daily.get("wind_speed_10m_max", [])

                daily_list = []
                for idx in range(min(7, len(dates))):
                    daily_list.append({
                        "date": dates[idx][5:],
                        "hs_max": round(float(hs_max_list[idx] or hs), 2),
                        "tp_max": round(float(tp_max_list[idx] or tp), 1),
                        "w_max": round(float(w_max_list[idx] or w_spd), 1)
                    })

                res.update({
                    "hs": round(hs, 2), "tp": round(tp, 1), "w": round(w_spd, 1),
                    "wind_dir": round(w_dir, 0), "monsoon_angle": round(delta_theta, 1),
                    "pressure": round(pressure, 1), "pressure_3h": p_3h, "tide": tide_est,
                    "daily_forecast": daily_list,
                    "pm_forecast": {
                        "pm_hs_max": pm_hs_max, "pm_tp_max": pm_tp_max,
                        "hs_slope_3h": hs_slope_3h, "afternoon_risk": afternoon_risk,
                        "risk_label": risk_label
                    },
                    "data_source": src_tag
                })
        except Exception:
            pass
        return res

    def fetch_typhoon_status(self, pressure: float) -> dict:
        emergency_centers = {"central": "未開設", "yilan": "未開設", "new_taipei": "未開設"}
        if self.cwa_api_key:
            for dataset_id in ["W-C0034-001", "W-C0034-005"]:
                try:
                    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{dataset_id}?Authorization={self.cwa_api_key}"
                    r = requests.get(url, timeout=4)
                    if r.status_code == 200:
                        records = r.json().get("records", {}).get("tropicalCyclones", {}).get("tropicalCyclone", [])
                        if records:
                            tc = records[0]
                            name = tc.get("cwaTyphoonName") or tc.get("typhoonName") or "熱帶氣旋"
                            dist_km = 450.0
                            fix = tc.get("analysisData", {}).get("fix", [])
                            if fix:
                                last_fix = fix[-1]
                                coord_str = last_fix.get("coordinate", "")
                                parts = [float(x) for x in re.findall(r"[\d.]+", coord_str)]
                                if len(parts) >= 2:
                                    lon_tc, lat_tc = (parts[0], parts[1]) if parts[0] > 60 else (parts[1], parts[0])
                                    dist_km = self._haversine_km(self.lat, self.lon, lat_tc, lon_tc)
                            if dist_km < 150.0:
                                emergency_centers = {"central": "一級開設", "yilan": "一級開設", "new_taipei": "一級開設"}
                            elif dist_km < 300.0:
                                emergency_centers = {"central": "二級開設", "yilan": "二級開設", "new_taipei": "二級開設"}
                            return {
                                "warning": "🔴 颱風警報發布中",
                                "name": name,
                                "distance": f"{dist_km:.1f} km",
                                "dist_km": dist_km,
                                "eta": "請依海陸警通報",
                                "emergency_centers": emergency_centers
                            }
                except Exception:
                    continue
        if pressure < 1002.0:
            return {"warning": "🟡 低壓擾動注意", "name": "熱帶/鋒面低壓系統", "distance": "< 450 km", "dist_km": 450.0, "eta": "約 12.0 小時", "emergency_centers": emergency_centers}
        return {"warning": "🟢 無警報 (未發布)", "name": "無近臺熱帶氣旋", "distance": "> 1,200 km", "dist_km": 1200.0, "eta": "無暴風圈威脅", "emergency_centers": emergency_centers}

    def estimate_swell_macro_dynamics(self, hs: float, tp: float, tide: float, pm_forecast: dict = None) -> dict:
        g = 9.81
        cg_speed = (g * tp) / (4 * np.pi)
        cg_knots = cg_speed * 1.94384
        energy_flux = hs**2 * tp
        pm_forecast = pm_forecast or {}

        now = datetime.now(CST)
        is_swell_alert = (tp >= 12.0 and hs >= 1.13) or bool(pm_forecast.get("afternoon_risk", False))

        if tp >= 12.0 and hs >= 1.13:
            start_impact = now + timedelta(hours=1.0)
            end_impact = start_impact + timedelta(hours=3.5)
            status_tag = "🔴 高度漫頂共振期 (Kd=1.00)"
            timeline_str = f"{start_impact.strftime('%H:%M')} - {end_impact.strftime('%H:%M')} CST (長浪共振峰值)"
            advice = f"長浪週期 Tp={tp}s >= 12.0s (群速 {cg_knots:.1f}節, 能量流 {energy_flux:.1f}) 消能崩解，嚴防港池共振與引橋越浪。"
        elif pm_forecast.get("afternoon_risk"):
            status_tag = "🟡 午後長浪湧升預警"
            timeline_str = "11:20 止登 / 14:20 強制清島 (逐時波譜顯示午後轉惡)"
            advice = f"目前波高 Hs={hs}m 尚可，但未來 3h 斜率 {pm_forecast.get('hs_slope_3h', 0):+.2f}m，午後預估達 Hs={pm_forecast.get('pm_hs_max')}m / Tp={pm_forecast.get('pm_tp_max')}s，啟動 Q3 動態開窗防範午後臨時封島。"
        else:
            status_tag = "🟢 海象平穩受控"
            timeline_str = "無明顯長浪湧浪漫頂威脅"
            advice = f"目前外海波高 Hs={hs}m、週期 Tp={tp}s，經地形折算後符合靠泊安全線，可維持常規登島作業。"

        return {
            "is_swell_alert": is_swell_alert, "status_tag": status_tag,
            "impact_window_str": timeline_str, "advice": advice,
            "cg_speed_ms": round(cg_speed, 2), "cg_knots": round(cg_knots, 1),
            "energy_flux": round(energy_flux, 2)
        }

    def harvest_telemetry(self, raw_input: dict = None) -> dict:
        raw_input = raw_input or {}
        announcement = self.fetch_official_announcement(raw_input.get("override_announcement"))
        live_wx = self.fetch_live_marine_and_weather()

        hs = float(raw_input.get("hs", live_wx["hs"]))
        tp = float(raw_input.get("tp", live_wx["tp"]))
        tide = float(raw_input.get("tide", live_wx["tide"]))
        w = float(raw_input.get("w", live_wx["w"]))
        monsoon_angle = float(raw_input.get("monsoon_angle", live_wx["monsoon_angle"]))
        pressure = float(raw_input.get("pressure", live_wx["pressure"]))
        pressure_3h = float(raw_input.get("pressure_3h", live_wx["pressure_3h"]))
        pm_forecast = live_wx.get("pm_forecast", {})

        auto_cv = round(max(0.0, (hs - 1.25) * 1.55 + (0.60 if tp >= 12.0 and hs >= 1.5 else 0.0)), 2)
        cctv_cv_rate = float(raw_input.get("cctv_cv_rate", auto_cv))

        res = {
            "hs": hs, "tp": tp, "w": w, "wind_dir": live_wx.get("wind_dir", 45.0),
            "tide": tide, "monsoon_angle": monsoon_angle, "pressure": pressure,
            "pressure_3h": pressure_3h, "cctv_cv_rate": cctv_cv_rate,
            "v_speed_kts": float(raw_input.get("v_speed_kts", 12.5)),
            "passenger_count": int(raw_input.get("passenger_count", 150)),
            "high_tide_hour": float(raw_input.get("high_tide_hour", 10.0)),
            "daily_forecast": live_wx.get("daily_forecast", []),
            "pm_forecast": pm_forecast,
            "data_source": live_wx.get("data_source", "live"),
            "typhoon_info": self.fetch_typhoon_status(pressure),
            "official_announcement": announcement,
            "swell_forecast": self.estimate_swell_macro_dynamics(hs, tp, tide, pm_forecast)
        }
        for k in ["wufu_lat", "wufu_lon", "wufu_sog", "tsunami_pulse_alert", "local_pga_gal", "visibility_m"]:
            if k in raw_input:
                res[k] = raw_input[k]
        return res
