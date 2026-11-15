import os
import json
import math
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

CST = timezone(timedelta(hours=8))

class GemVesselAgent:
    def __init__(self, track_db_path: str = "data/wufu_track.json", ais_api_url: str = None):
        self.track_db_path = track_db_path
        self.ais_api_url = ais_api_url or os.environ.get("AIS_API_URL")
        self.official_vessel = {
            "name": "東北角五福號", "mmsi": "416017708", "call_sign": "BR5216",
            "kind": "公務小船", "draft_m": 1.20
        }
        self.pier_wushi = {"lat": 24.86872, "lon": 121.84154}
        self.pier_north = {"lat": 24.843727, "lon": 121.943732}
        self.pier_south = {"lat": 24.840441, "lon": 121.939794}

    @staticmethod
    def is_operational_boat_hours(dt: datetime = None) -> bool:
        dt = dt or datetime.now(CST)
        cur_min = dt.hour * 60 + dt.minute
        return (7 * 60 <= cur_min <= 16 * 60 + 30)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return float(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
        x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
             math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1)))
        return round((math.degrees(math.atan2(y, x)) + 360.0) % 360.0, 1)

    def fetch_realtime_ais_api(self) -> Optional[dict]:
        '''嘗試從外部真實 AIS API 端點取得 MMSI 416017708 經緯度與航速'''
        if not self.ais_api_url:
            return None
        try:
            resp = requests.get(self.ais_api_url, timeout=4)
            if resp.status_code == 200:
                payload = resp.json()
                records = payload if isinstance(payload, list) else payload.get("data", [payload])
                for item in records:
                    if str(item.get("mmsi", "")) == "416017708" or ("lat" in item and "lon" in item):
                        return {
                            "lat": float(item["lat"]),
                            "lon": float(item["lon"]),
                            "sog": float(item.get("sog", item.get("speed", 0.0))),
                            "source_tag": "AIS即時API"
                        }
        except Exception:
            pass
        return None

    def _update_and_load_track(self, lat: float, lon: float, sog: float, tag: str, is_real_ais: bool, dt: datetime) -> List[dict]:
        os.makedirs(os.path.dirname(self.track_db_path) or ".", exist_ok=True)
        history = []
        if os.path.exists(self.track_db_path):
            try:
                with open(self.track_db_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        # 僅在真實 AIS 變動或為首筆初始化時追加軌跡，避免相同靜態點重複洗版
        should_append = True
        if history:
            last = history[-1]
            if abs(last.get("lat", 0) - round(lat, 6)) < 1e-5 and abs(last.get("lon", 0) - round(lon, 6)) < 1e-5 and last.get("tag") == tag:
                should_append = False

        if should_append:
            history.append({
                "ts": dt.isoformat(),
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "sog": round(sog, 2),
                "tag": tag,
                "is_real_ais": is_real_ais
            })
            history = history[-15:]
            tmp_path = f"{self.track_db_path}.tmp_{os.getpid()}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.track_db_path)
        return history

    def analyze_trajectory_vector(self, track_history: List[dict], is_real_ais: bool) -> Dict[str, Any]:
        if not is_real_ais:
            return {
                "vector_state": "HYDRO_FALLBACK",
                "vector_desc": "🛰️ 待接通真實AIS (目前為水文推演備援)",
                "delta_dist_m": 0.0,
                "cog_deg": None
            }
        if len(track_history) < 2:
            return {
                "vector_state": "INITIAL_POINT",
                "vector_desc": "📡 AIS首筆定位建立中 (待累積軌跡)",
                "delta_dist_m": 0.0,
                "cog_deg": None
            }

        p_prev, p_curr = track_history[-2], track_history[-1]
        d_prev = min(
            self._haversine_distance(p_prev["lat"], p_prev["lon"], self.pier_north["lat"], self.pier_north["lon"]),
            self._haversine_distance(p_prev["lat"], p_prev["lon"], self.pier_south["lat"], self.pier_south["lon"])
        )
        d_curr = min(
            self._haversine_distance(p_curr["lat"], p_curr["lon"], self.pier_north["lat"], self.pier_north["lon"]),
            self._haversine_distance(p_curr["lat"], p_curr["lon"], self.pier_south["lat"], self.pier_south["lon"])
        )
        delta_d = round(d_curr - d_prev, 1)
        moved_m = self._haversine_distance(p_prev["lat"], p_prev["lon"], p_curr["lat"], p_curr["lon"])
        cog = self._calculate_bearing(p_prev["lat"], p_prev["lon"], p_curr["lat"], p_curr["lon"]) if moved_m > 15.0 else None
        sog = float(p_curr.get("sog", 0.0))

        if d_curr <= 180.0 and sog <= 1.5:
            state = "STATIONARY_AT_PIER"
            desc = "🟢 軌跡穩定駐泊碼頭戒護 (Δd≈0m)"
        elif delta_d > 300.0 and sog >= 3.0 and (cog is not None and 235.0 <= cog <= 320.0):
            state = "RETREATING_TO_WUSHI"
            desc = f"🔴 軌跡返航烏石港 (COG {cog}°, Δd=+{delta_d}m) [早退/封島鐵證]"
        elif delta_d < -300.0 and sog >= 3.0 and (cog is not None and 80.0 <= cog <= 140.0):
            state = "APPROACHING_ISLAND"
            desc = f"🚢 軌跡駛向龜山島 (COG {cog}°, Δd={delta_d}m) [準備開島]"
        elif 200.0 < d_curr <= 1000.0 and sog > 2.0 and abs(delta_d) < 150.0:
            state = "LOITERING_FAILED_DOCK"
            desc = f"⚠️ 島周繞行無法靠泊 (距岸 {round(d_curr)}m, SOG {sog}kt)"
        else:
            state = "BERTHED_OR_IDLE"
            desc = f"⚓ 靜止待命 (距島 {round(d_curr)}m, Δd={delta_d}m)"

        return {
            "vector_state": state,
            "vector_desc": desc,
            "delta_dist_m": delta_d,
            "cog_deg": cog
        }

    def _infer_vessel_position_from_hydrodynamics(self, telemetry: dict, dt: datetime) -> dict:
        hs = float(telemetry.get("hs", 1.15))
        tp = float(telemetry.get("tp", 8.5))
        w = float(telemetry.get("w", 5.5))
        theta = float(telemetry.get("monsoon_angle", 35.0))

        kd_n = 1.00 if tp >= 12.0 else (0.75 if theta < 45.0 else 1.00)
        kd_s = 0.75 if tp >= 12.0 else 0.55
        hs_n = hs * kd_n
        hs_s = hs * kd_s
        weff = w * abs(math.cos(math.radians(theta)))

        in_hours = self.is_operational_boat_hours(dt)
        if in_hours:
            if hs_n <= 0.95 and weff <= 8.50:
                return {"lat": 24.84375, "lon": 121.94378, "sog": 0.1, "source_tag": "水文推演備援·北岸"}
            elif hs_s <= 1.13 and weff <= 10.17:
                return {"lat": 24.84048, "lon": 121.93985, "sog": 0.1, "source_tag": "水文推演備援·南岸"}
        return {"lat": 24.86872, "lon": 121.84154, "sog": 0.0, "source_tag": "水文推演備援·母港"}

    def evaluate_docking_status(self, off_lat: float, off_lon: float, sog: float, source_tag: str, is_real_ais: bool, dt: datetime = None) -> Dict[str, Any]:
        dt = dt or datetime.now(CST)
        in_boat_hours = self.is_operational_boat_hours(dt)

        dist_wushi = self._haversine_distance(off_lat, off_lon, self.pier_wushi["lat"], self.pier_wushi["lon"])
        dist_north = self._haversine_distance(off_lat, off_lon, self.pier_north["lat"], self.pier_north["lon"])
        dist_south = self._haversine_distance(off_lat, off_lon, self.pier_south["lat"], self.pier_south["lon"])

        is_docked_north = (dist_north <= 180.0 and sog <= 1.5)
        is_docked_south = (dist_south <= 180.0 and sog <= 1.5)
        is_docked_island = is_docked_north or is_docked_south

        if is_docked_north:
            state_desc = f"🟢 五福號靠泊北岸戒護中 ({source_tag})"
            dock_code = "DOCKED_NORTH"
            implied_open = True
        elif is_docked_south:
            state_desc = f"🟡 五福號靠泊南岸戒護中 ({source_tag})"
            dock_code = "DOCKED_SOUTH"
            implied_open = True
        elif dist_wushi <= 1200.0 and sog <= 0.8:
            if in_boat_hours:
                state_desc = f"🔴 五福號船班時段停泊烏石港未出港 ({source_tag})"
                dock_code = "BERTHED_WUSHI_CLOSED"
            else:
                state_desc = f"🌙 五福號非營運時段停泊烏石港母港 ({source_tag})"
                dock_code = "BERTHED_WUSHI_OFFHOURS"
            implied_open = False
        elif dist_north <= 900.0 or dist_south <= 900.0:
            state_desc = f"⚠️ 五福號島周繞行無法靠泊 ({source_tag})"
            dock_code = "PATROLLING_FAILED"
            implied_open = False
        else:
            state_desc = f"🚢 五福號航道往返航行中 ({source_tag})"
            dock_code = "EN_ROUTE"
            implied_open = False

        return {
            "dist_wushi_m": round(dist_wushi, 1),
            "dist_north_m": round(dist_north, 1),
            "dist_south_m": round(dist_south, 1),
            "is_real_ais": is_real_ais,
            "is_docked_island": is_docked_island,
            "in_boat_hours": in_boat_hours,
            "implied_official_open": implied_open,
            "dock_code": dock_code,
            "dock_desc": state_desc
        }

    def track_and_back_calculate(self, telemetry: dict, dt: datetime = None) -> dict:
        dt = dt or datetime.now(CST)
        off = self.official_vessel
        if "wufu_lat" in telemetry and "wufu_lon" in telemetry:
            lat = float(telemetry["wufu_lat"])
            lon = float(telemetry["wufu_lon"])
            sog = float(telemetry.get("wufu_sog", 0.2))
            tag = "AIS即時傳入"
            is_real_ais = True
        else:
            live_ais = self.fetch_realtime_ais_api()
            if live_ais:
                lat, lon, sog, tag = live_ais["lat"], live_ais["lon"], live_ais["sog"], live_ais["source_tag"]
                is_real_ais = True
            else:
                inferred = self._infer_vessel_position_from_hydrodynamics(telemetry, dt)
                lat, lon, sog, tag = inferred["lat"], inferred["lon"], inferred["sog"], inferred["source_tag"]
                is_real_ais = False

        track_history = self._update_and_load_track(lat, lon, sog, tag, is_real_ais, dt)
        traj_eval = self.analyze_trajectory_vector(track_history, is_real_ais)
        dock_eval = self.evaluate_docking_status(lat, lon, sog, tag, is_real_ais, dt)

        return {
            "official_wufu": {
                "name": off["name"], "mmsi": off["mmsi"],
                "coord_str": f"{lat:.5f}° N, {lon:.5f}° E",
                "sog_knots": sog,
                **dock_eval,
                **traj_eval
            },
            "wushi_port_fleet_flux": {"v_flux_ships_per_hour": 42.0 if dock_eval["implied_official_open"] else 0.0}
        }
