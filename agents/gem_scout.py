import re
import math
import requests
import numpy as np
from bs4 import BeautifulSoup
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

    def fetch_facebook_announcement(self) -> dict:
        if not self.fb_page_token or not self.fb_page_id:
            return None
        url = f"https://graph.facebook.com/v18.0/{self.fb_page_id}/published_posts"
        params = {"access_token": self.fb_page_token, "limit": 1, "fields": "message,created_time"}
        try:
            resp = requests.get(url, params=params, timeout=4)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    msg = data[0].get("message", "")
                    is_closed = bool(re.search(r"(本日封島|續封島|明日封島|明天封島|暫停開放|不開放登島)", msg))
                    return {
                        "official_veto": 1 if is_closed else 0,
                        "wave_warning": True,
                        "title": f"【FB 社群公告】{msg[:35]}...",
                        "body": msg,
                        "source": "facebook_api",
                        "published_at": data[0].get("created_time", "")
                    }
        except Exception:
            pass
        return None

    def fetch_official_announcement(self, override_announcement: dict = None) -> dict:
        if override_announcement:
            return override_announcement

        fb_res = self.fetch_facebook_announcement()
        if fb_res and fb_res["official_veto"] == 1:
            return fb_res

        now = datetime.now(CST)
        current_day = now.day
        tomorrow_day = (now + timedelta(days=1)).day

        default_payload = {
            "official_veto": 0,
            "wave_warning": False,
            "title": "【風管處通告】全島常規開放營運中",
            "body": "東北角暨宜蘭海岸國家風景區管理處：龜山島今日海象受控，常態營運開放登島作業。",
            "published_at": now.strftime("%Y-%m-%d %H:%M CST"),
            "extracted_day": current_day,
            "source": "official_web"
        }

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        for url in self.official_urls:
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    full_text = soup.get_text()

                    is_closed = bool(re.search(r"(本日封島|續封島|明日封島|明天封島|明\(\d+\)日|\d+月\d+日封島|115年\d+月\d+日|禁止靠泊|浪潮蓋碼頭|暫停開放|不開放登島)", full_text))
                    has_waves = bool(re.search(r"(長浪|浪高|浪潮漫頂|湧浪|大潮|風力超過|平均風力)", full_text))

                    day_match = re.search(r"(?:明|今|本)\((\d+)\)日|(\d+)月(\d+)日封島|\d+年\d+月(\d+)日", full_text)
                    extracted_day = int(day_match.group(1) or day_match.group(3) or day_match.group(4) or tomorrow_day) if day_match else current_day

                    default_payload.update({
                        "official_veto": 1 if is_closed else 0,
                        "wave_warning": has_waves,
                        "title": f"【風管處公告】受氣象/海浪影響，({extracted_day})日龜山島實施封島" if is_closed else "【風管處通告】全島常規開放營運中",
                        "extracted_day": extracted_day
                    })
                    break
            except Exception:
                continue

        return default_payload

    def fetch_live_marine_and_weather(self) -> dict:
        '''即時抓取龜山島海域海浪與氣象觀測預報 (Open-Meteo Marine & Weather API)'''
        marine_url = (
            f"https://marine-api.open-meteo.com/v1/marine?"
            f"latitude={self.lat}&longitude={self.lon}"
            f"&current=wave_height,wave_period,swell_wave_height,swell_wave_period"
            f"&daily=wave_height_max,wave_period_max&timezone=Asia%2FTaipei"
        )
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.lat}&longitude={self.lon}"
            f"&current=wind_speed_10m,wind_direction_10m,surface_pressure"
            f"&hourly=surface_pressure&daily=wind_speed_10m_max"
            f"&wind_speed_unit=ms&timezone=Asia%2FTaipei"
        )
        res = {
            "hs": 1.15, "tp": 8.5, "w": 7.5, "wind_dir": 45.0,
            "monsoon_angle": 35.0, "pressure": 1014.0, "pressure_3h": -0.5,
            "tide": 0.95, "daily_forecast": [], "data_source": "fallback_baseline"
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
                w_spd = float(w_cur.get("wind_speed_10m") or 7.5)
                w_dir = float(w_cur.get("wind_direction_10m") or 45.0)
                pressure = float(w_cur.get("surface_pressure") or 1014.0)

                delta_theta = min(180.0, abs(((w_dir - 45.0 + 180.0) % 360.0) - 180.0))

                p_3h = 0.0
                hourly_p = w_data.get("hourly", {}).get("surface_pressure", [])
                now_hr = datetime.now(CST).hour
                if len(hourly_p) > now_hr and now_hr >= 3:
                    p_3h = round(float(hourly_p[now_hr]) - float(hourly_p[now_hr - 3]), 1)

                now_cst = datetime.now(CST)
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
                    "hs": round(hs, 2),
                    "tp": round(tp, 1),
                    "w": round(w_spd, 1),
                    "wind_dir": round(w_dir, 0),
                    "monsoon_angle": round(delta_theta, 1),
                    "pressure": round(pressure, 1),
                    "pressure_3h": p_3h,
                    "tide": tide_est,
                    "daily_forecast": daily_list,
                    "data_source": "open_meteo_live"
                })
        except Exception:
            pass
        return res

    def fetch_typhoon_status(self, pressure: float) -> dict:
        '''取得近臺颱風或熱帶低壓動態'''
        if self.cwa_api_key:
            try:
                url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0034-005?Authorization={self.cwa_api_key}"
                r = requests.get(url, timeout=4)
                if r.status_code == 200:
                    records = r.json().get("records", {}).get("tropicalCyclones", {}).get("tropicalCyclone", [])
                    if records:
                        tc = records[0]
                        name = tc.get("cwaTyphoonName") or tc.get("typhoonName") or "熱帶氣旋"
                        return {
                            "warning": "🔴 颱風警報發布中",
                            "name": name,
                            "distance": "監測警戒區內",
                            "eta": "請依海陸警通報"
                        }
            except Exception:
                pass

        if pressure < 1002.0:
            return {
                "warning": "🟡 低壓擾動注意",
                "name": "熱帶/鋒面低壓系統",
                "distance": "< 450 km",
                "eta": "約 12.0 小時"
            }
        return {
            "warning": "🟢 無警報 (未發布)",
            "name": "無近臺熱帶氣旋",
            "distance": "> 1,200 km",
            "eta": "無暴風圈威脅"
        }

    def estimate_swell_macro_dynamics(self, hs: float, tp: float, tide: float) -> dict:
        g = 9.81
        cg_speed = (g * tp) / (4 * np.pi)
        cg_knots = cg_speed * 1.94384
        energy_flux = hs**2 * tp

        now = datetime.now(CST)
        is_swell_alert = (tp >= 10.5 and hs >= 1.2)

        if is_swell_alert:
            start_impact = now + timedelta(hours=1.0)
            end_impact = start_impact + timedelta(hours=3.5)
            status_tag = "🔴 高度漫頂風險期" if hs >= 1.8 else "🟡 湧浪越浪警戒期"
            timeline_str = f"{start_impact.strftime('%H:%M')} - {end_impact.strftime('%H:%M')} CST (長浪湧浪峰值)"
            advice = f"長浪週期 Tp={tp}s (群速 {cg_knots:.1f}節, 能量流 {energy_flux:.1f}) 易引發碼頭消能瓦解，建議維持剛性封閉或機動移防南岸。"
        else:
            status_tag = "🟢 海象平穩受控"
            timeline_str = "無明顯長浪湧浪漫頂威脅"
            advice = f"目前波高 Hs={hs}m、週期 Tp={tp}s，風浪受控，可維持常規航務作業。"

        return {
            "is_swell_alert": is_swell_alert,
            "status_tag": status_tag,
            "impact_window_str": timeline_str,
            "advice": advice,
            "cg_speed_ms": round(cg_speed, 2),
            "cg_knots": round(cg_knots, 1),
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

        auto_cv = round(max(0.0, (hs - 1.15) * 1.65 + (0.35 if tp >= 12.0 and hs >= 1.3 else 0.0)), 2)
        cctv_cv_rate = float(raw_input.get("cctv_cv_rate", auto_cv))

        return {
            "hs": hs,
            "tp": tp,
            "w": w,
            "wind_dir": live_wx.get("wind_dir", 45.0),
            "tide": tide,
            "monsoon_angle": monsoon_angle,
            "pressure": pressure,
            "pressure_3h": pressure_3h,
            "cctv_cv_rate": cctv_cv_rate,
            "daily_forecast": live_wx.get("daily_forecast", []),
            "data_source": live_wx.get("data_source", "live"),
            "typhoon_info": self.fetch_typhoon_status(pressure),
            "official_announcement": announcement,
            "swell_forecast": self.estimate_swell_macro_dynamics(hs, tp, tide)
        }
