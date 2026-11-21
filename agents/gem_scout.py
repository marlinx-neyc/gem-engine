import re
import time
import math
import urllib3
import requests
import numpy as np
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from email.utils import parsedate_to_datetime
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
from datetime import datetime, timedelta, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CST = timezone(timedelta(hours=8))

class GemScoutAgent:
    def __init__(self, cwa_api_key: str = None, fb_page_token: str = None, fb_page_id: str = None):
        self.cwa_api_key = cwa_api_key or ""
        self.fb_page_token = fb_page_token or ""
        self.fb_page_id = fb_page_id or "necoast.nsa"
        self.lat = 24.8425
        self.lon = 121.9510
        self.official_urls = [
            "https://events.necoast-nsa.gov.tw/coast/",
            "https://events.necoast-nsa.gov.tw/coast/index.aspx",
            "https://www.necoast-nsa.gov.tw/News.aspx?a=6&l=1",
            "https://www.necoast-nsa.gov.tw/Articles.aspx?a=5&l=1",
            "https://www.necoast-nsa.gov.tw/Articles.aspx?a=319&l=1",
            "https://www.necoast-nsa.gov.tw/"
        ]
        self.news_rss_urls = [
            "https://news.google.com/rss/search?q=%E9%BE%9C%E5%B1%B1%E5%B3%B6+(%E5%B0%81%E5%B3%B6+OR+%E5%81%9C%E8%88%AA+OR+%E6%9D%B1%E5%8C%97%E8%A7%92%E9%A2%A8%E7%AE%A1%E8%99%95)+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
            "https://news.google.com/rss/search?q=site:facebook.com+%E6%9D%B1%E5%8C%97%E8%A7%92%E4%B9%8B%E5%8F%8B+%E9%BE%9C%E5%B1%B1%E5%B3%B6&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        ]

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)

    @staticmethod
    def _extract_closure_windows(raw_text: str) -> list:
        # 從長段落或導覽列混合文字中精準切割出包含「龜山島」與封島關鍵字的前後視窗
        normalized = re.sub(r"\s+", " ", raw_text).strip()
        windows = []
        for m in re.finditer(r"龜山島", normalized):
            start = max(0, m.start() - 60)
            end = min(len(normalized), m.end() + 120)
            seg = normalized[start:end].strip()
            if re.search(r"(封島|禁止靠泊|浪潮蓋碼頭|暫停開放|不開放登島|暫停登島|停止開放|預警性封島)", seg):
                if seg not in windows:
                    windows.append(seg)
        return windows

    def _check_date_relevance(self, text: str, now_cst: datetime, pub_dt: datetime = None) -> dict:
        today_m, today_d = now_cst.month, now_cst.day
        roc_y = now_cst.year - 1911
        tmr = now_cst + timedelta(days=1)
        tmr_m, tmr_d = tmr.month, tmr.day

        today_pat = (
            rf"(本日封島|今日封島|今天封島|當日封島|下午封島|封島半天|午後封島|"
            rf"今\s*[\(（]?\s*0?{today_d}\s*[\)）]?\s*日|"
            rf"0?{today_m}\s*月\s*0?{today_d}\s*日|"
            rf"(?<![\d/])0?{today_m}/0?{today_d}(?![\d/])|"
            rf"{roc_y}[./-]0?{today_m}[./-]0?{today_d}|"
            rf"{now_cst.year}[./-]0?{today_m}[./-]0?{today_d})"
        )
        tmr_pat = (
            rf"(明日封島|明天封島|續封島|次日封島|"
            rf"明\s*[\(（]?\s*0?{tmr_d}\s*[\)）]?\s*日|"
            rf"0?{tmr_m}\s*月\s*0?{tmr_d}\s*日|"
            rf"(?<![\d/])0?{tmr_m}/0?{tmr_d}(?![\d/])|"
            rf"{roc_y}[./-]0?{tmr_m}[./-]0?{tmr_d})"
        )

        # 排除僅針對「南岸碼頭/401步道局部設施災損」而非全島封島之歷史公告
        if re.search(r"(401登山步道及南岸碼頭.*暫停開放|南岸碼頭.*暫停開放)", text) and not re.search(r"(封島|不開放登島|暫停登島)", text):
            return {"valid": False, "is_today": False, "is_tmr": False, "scope": "SOUTH_PIER_ONLY", "stale_filtered": False, "reason": "partial_facility_notice"}

        if pub_dt is not None:
            age_hours = (now_cst - pub_dt).total_seconds() / 3600.0
            if age_hours > 18.0 and not re.search(rf"({today_pat}|續封)", text):
                return {"valid": False, "is_today": False, "is_tmr": False, "scope": "FULL_DAY", "stale_filtered": True, "reason": f"expired_{age_hours:.1f}h"}

        is_today = bool(re.search(today_pat, text))
        is_tmr = bool(re.search(tmr_pat, text))
        scope = "AFTERNOON" if re.search(r"(下午封島|封島半天|午後封島|12:00)", text) else "FULL_DAY"

        explicit_dates = re.findall(r"(0?\d{1,2})\s*月\s*(0?\d{1,2})\s*日", text)
        explicit_slashes = re.findall(r"(?<!\d)(0?\d{1,2})/(0?\d{1,2})(?!\d)", text)
        all_md = [(int(m), int(d)) for m, d in (explicit_dates + explicit_slashes) if 1 <= int(m) <= 12 and 1 <= int(d) <= 31]

        if all_md:
            has_other_date = any((m, d) not in [(today_m, today_d), (tmr_m, tmr_d)] for m, d in all_md)
            if has_other_date and not is_today and not is_tmr:
                return {"valid": False, "is_today": False, "is_tmr": False, "scope": scope, "stale_filtered": True, "reason": f"other_date_{all_md}"}

        if not all_md and not is_today and not is_tmr:
            if re.search(r"(封島一日|封島一天|實施封島|宣布封島|公告封島|暫停開放登島|不開放登島|暫停登島|預警性封島)", text):
                return {"valid": True, "is_today": True, "is_tmr": False, "scope": scope, "stale_filtered": False, "reason": "dateless_active_banner"}
            return {"valid": False, "is_today": False, "is_tmr": False, "scope": scope, "stale_filtered": False, "reason": "no_date_and_ambiguous"}

        return {"valid": True, "is_today": is_today, "is_tmr": is_tmr, "scope": scope, "stale_filtered": False, "reason": "matched_date"}

    def fetch_facebook_announcement(self, diag_logs: list = None) -> dict:
        # 雙軌 FB 查詢：1) Meta Graph API (若有 Token) -> 2) mbasic.facebook.com/necoast.nsa 公開頁免 Token 穿透
        diag_logs = diag_logs if diag_logs is not None else []
        now_cst = datetime.now(CST)

        if self.fb_page_token and self.fb_page_id:
            url = f"https://graph.facebook.com/v19.0/{self.fb_page_id}/published_posts"
            params = {"access_token": self.fb_page_token, "limit": 5, "fields": "message,created_time"}
            try:
                resp = requests.get(url, params=params, timeout=5)
                diag_logs.append(f"fb_graph:{resp.status_code}")
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
                        if "龜山島" in msg and re.search(r"(封島|暫停開放|不開放登島|暫停登島)", msg):
                            rel = self._check_date_relevance(msg, now_cst, pub_dt=pub_dt)
                            if rel["valid"]:
                                return {
                                    "official_veto": 1 if rel["is_today"] else 0,
                                    "tomorrow_veto": 1 if rel["is_tmr"] else 0,
                                    "scope": rel["scope"],
                                    "wave_warning": True,
                                    "title": f"【FB 東北角之友公告】{msg[:40]}...",
                                    "body": msg,
                                    "source": "facebook_graph_api",
                                    "published_at": pub_dt.strftime("%Y-%m-%d %H:%M CST") if pub_dt else created_raw
                                }
            except Exception as e:
                diag_logs.append(f"fb_graph:ERR({type(e).__name__})")
        else:
            diag_logs.append("fb_graph:NO_TOKEN")

        fb_slug = self.fb_page_id if self.fb_page_id and not self.fb_page_id.isdigit() else "necoast.nsa"
        mbasic_url = f"https://mbasic.facebook.com/{fb_slug}"
        try:
            resp = requests.get(
                mbasic_url,
                headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36", "Accept-Language": "zh-TW,zh;q=0.9"},
                timeout=6
            )
            diag_logs.append(f"fb_mbasic:{resp.status_code}")
            if resp.status_code == 200 and "龜山島" in resp.text:
                clean_txt = re.sub(r"<[^>]+>", " ", resp.text)
                for seg in self._extract_closure_windows(clean_txt):
                    rel = self._check_date_relevance(seg, now_cst)
                    if rel["valid"] and (rel["is_today"] or rel["is_tmr"]):
                        return {
                            "official_veto": 1 if rel["is_today"] else 0,
                            "tomorrow_veto": 1 if rel["is_tmr"] else 0,
                            "scope": rel["scope"],
                            "wave_warning": True,
                            "title": f"【FB 東北角之友公開貼文】{seg[:42]}...",
                            "body": seg,
                            "source": "facebook_public_scrape",
                            "published_at": now_cst.strftime("%Y-%m-%d %H:%M CST")
                        }
        except Exception as e:
            diag_logs.append(f"fb_mbasic:ERR({type(e).__name__})")

        return None

    def _fetch_google_news_rss_fallback(self, now_cst: datetime, diag_logs: list) -> dict:
        # 穿透海外機房 IP 限制：透過 Google News 台灣新聞與 FB 索引 RSS 捕捉風管處最新封島快訊
        for idx, rss_url in enumerate(self.news_rss_urls):
            try:
                resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
                diag_logs.append(f"rss_{idx+1}:{resp.status_code}")
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    for item in root.findall(".//item")[:8]:
                        title = (item.findtext("title") or "").strip()
                        pub_raw = (item.findtext("pubDate") or "").strip()
                        pub_dt = None
                        if pub_raw:
                            try:
                                pub_dt = parsedate_to_datetime(pub_raw).astimezone(CST)
                            except Exception:
                                pub_dt = None
                        if "龜山島" in title and re.search(r"(封島|暫停開放|不開放登島|暫停登島|預警性封島)", title):
                            rel = self._check_date_relevance(title, now_cst, pub_dt=pub_dt)
                            if rel["valid"] and rel["is_today"]:
                                return {
                                    "official_veto": 1,
                                    "tomorrow_veto": 1 if rel["is_tmr"] else 0,
                                    "scope": rel["scope"],
                                    "wave_warning": True,
                                    "title": f"【官方/媒體快訊】{title[:55]}",
                                    "body": f"{title} ({pub_dt.strftime('%Y-%m-%d %H:%M CST') if pub_dt else pub_raw})",
                                    "source": f"google_news_rss_{idx+1}",
                                    "matched_url": rss_url,
                                    "filter_reason": rel["reason"]
                                }
            except Exception as e:
                diag_logs.append(f"rss_{idx+1}:ERR({type(e).__name__})")
        return None

    def fetch_official_announcement(self, override_announcement: dict = None) -> dict:
        if override_announcement:
            return override_announcement

        now = datetime.now(CST)
        current_day = now.day
        tomorrow_day = (now + timedelta(days=1)).day
        diag_logs = []

        fb_res = self.fetch_facebook_announcement(diag_logs)
        if fb_res and (fb_res.get("official_veto") == 1 or fb_res.get("tomorrow_veto") == 1):
            fb_res["scraper_diagnostics"] = {
                "checked_at": now.strftime("%Y-%m-%d %H:%M:%S CST"),
                "matched_url": fb_res.get("source", "facebook"),
                "http_statuses": diag_logs,
                "raw_snippet": fb_res.get("body", "")[:140],
                "filter_reason": "fb_matched"
            }
            return fb_res

        default_payload = {
            "official_veto": 0,
            "tomorrow_veto": 0,
            "scope": "FULL_DAY",
            "wave_warning": False,
            "south_pier_closed_damage": True,
            "title": "【風管處通告】北岸開放常規營運（南岸碼頭災損封閉中）",
            "body": "東北角暨宜蘭海岸國家風景區管理處：今日未檢出全島封島通告（註：南岸碼頭及401步道因薔琵颱風災損暫停開放）。",
            "published_at": now.strftime("%Y-%m-%d %H:%M CST"),
            "extracted_day": current_day,
            "source": "official_web",
            "scraper_diagnostics": {
                "checked_at": now.strftime("%Y-%m-%d %H:%M:%S CST"),
                "matched_url": "none",
                "http_statuses": diag_logs,
                "raw_snippet": "未檢出今日全島封島公告",
                "filter_reason": "no_active_closure_found"
            }
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
        buster = int(time.time())
        tmr_candidate = None
        urls_to_scan = list(self.official_urls)
        visited = set()

        while urls_to_scan:
            base_url = urls_to_scan.pop(0)
            if base_url in visited:
                continue
            visited.add(base_url)
            sep = "&" if "?" in base_url else "?"
            url = f"{base_url}{sep}_t={buster}"
            try:
                resp = requests.get(url, headers=headers, timeout=6, verify=False)
                short_name = base_url.split("//")[1][:28]
                diag_logs.append(f"{short_name}:{resp.status_code}")
                if resp.status_code == 200:
                    resp.encoding = resp.apparent_encoding or "utf-8"
                    raw_blocks = []
                    if HAS_BS4:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        for a_tag in soup.find_all("a", href=True):
                            a_txt = a_tag.get_text(" ", strip=True)
                            if "龜山島" in a_txt:
                                raw_blocks.append(a_txt)
                                href = a_tag["href"]
                                if "News-Content.aspx" in href or "Articles.aspx" in href:
                                    full_link = urljoin(base_url, href)
                                    if full_link not in visited and len(urls_to_scan) < 10:
                                        urls_to_scan.append(full_link)
                        for el in soup.find_all(["li", "h1", "h2", "h3", "p", "marquee", "span", "div"]):
                            txt = el.get_text(" ", strip=True)
                            if "龜山島" in txt:
                                raw_blocks.append(txt)
                    else:
                        clean_txt = re.sub(r"<[^>]+>", "\n", resp.text)
                        raw_blocks = [ln.strip() for ln in clean_txt.splitlines() if "龜山島" in ln]

                    windows = []
                    for blk in raw_blocks:
                        windows.extend(self._extract_closure_windows(blk))

                    for snippet in windows:
                        rel = self._check_date_relevance(snippet, now)
                        if rel["valid"] and rel["is_today"]:
                            scope_txt = "下午封島半天" if rel["scope"] == "AFTERNOON" else "實施封島"
                            default_payload.update({
                                "official_veto": 1,
                                "tomorrow_veto": 1 if rel["is_tmr"] else 0,
                                "scope": rel["scope"],
                                "wave_warning": True,
                                "title": f"【風管處公告】受海象影響，({current_day})日龜山島{scope_txt}",
                                "body": snippet,
                                "extracted_day": current_day,
                                "source": "official_web_live",
                                "scraper_diagnostics": {
                                    "checked_at": now.strftime("%Y-%m-%d %H:%M:%S CST"),
                                    "matched_url": base_url,
                                    "http_statuses": diag_logs,
                                    "raw_snippet": snippet[:140],
                                    "filter_reason": rel["reason"]
                                }
                            })
                            return default_payload
                        elif rel["valid"] and rel["is_tmr"] and tmr_candidate is None:
                            tmr_candidate = (base_url, snippet, rel)
            except Exception as e:
                diag_logs.append(f"{base_url.split('//')[1][:22]}:ERR({type(e).__name__})")
                continue

        rss_hit = self._fetch_google_news_rss_fallback(now, diag_logs)
        if rss_hit:
            default_payload.update({
                "official_veto": 1,
                "tomorrow_veto": rss_hit["tomorrow_veto"],
                "scope": rss_hit["scope"],
                "wave_warning": True,
                "title": rss_hit["title"],
                "body": rss_hit["body"],
                "extracted_day": current_day,
                "source": rss_hit["source"],
                "scraper_diagnostics": {
                    "checked_at": now.strftime("%Y-%m-%d %H:%M:%S CST"),
                    "matched_url": rss_hit["matched_url"],
                    "http_statuses": diag_logs,
                    "raw_snippet": rss_hit["body"][:140],
                    "filter_reason": rss_hit["filter_reason"]
                }
            })
            return default_payload

        if tmr_candidate:
            base_url, snippet, rel = tmr_candidate
            default_payload.update({
                "tomorrow_veto": 1,
                "wave_warning": True,
                "title": f"【風管處預告】明日({tomorrow_day})日龜山島實施封島",
                "body": snippet,
                "extracted_day": tomorrow_day,
                "scraper_diagnostics": {
                    "checked_at": now.strftime("%Y-%m-%d %H:%M:%S CST"),
                    "matched_url": base_url,
                    "http_statuses": diag_logs,
                    "raw_snippet": snippet[:140],
                    "filter_reason": rel["reason"]
                }
            })
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
