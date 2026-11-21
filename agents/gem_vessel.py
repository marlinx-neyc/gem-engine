import os
import ssl
import json
import math
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

try:
    import paho.mqtt.client as mqtt
    HAS_PAHO_MQTT = True
except ImportError:
    HAS_PAHO_MQTT = False

CST = timezone(timedelta(hours=8))

class GemVesselAgent:
    def __init__(
        self,
        track_db_path: str = "data/wufu_track.json",
        ais_api_url: str = None,
        tdx_client_id: str = None,
        tdx_client_secret: str = None,
        tdx_mm_id: str = None,
        tdx_mm_username: str = None,
        tdx_mm_pw: str = None
    ):
        self.track_db_path = track_db_path
        self.ais_api_url = (ais_api_url or os.environ.get("AIS_API_URL") or "").strip() or None
        self.tdx_client_id = (tdx_client_id or os.environ.get("TDX_CLIENT_ID") or "").strip() or None
        self.tdx_client_secret = (tdx_client_secret or os.environ.get("TDX_CLIENT_SECRET") or "").strip() or None
        self.tdx_mm_id = (tdx_mm_id or os.environ.get("TDX_MMID") or "").strip() or None
        self.tdx_mm_username = (tdx_mm_username or os.environ.get("TDX_MMUsername") or "").strip() or None
        self.tdx_mm_pw = (tdx_mm_pw or os.environ.get("TDX_MMPW") or "").strip() or None
        self._tdx_token_cache = {"token": None, "expires_at": 0.0}
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

    def _get_tdx_access_token(self, diag_logs: list) -> Optional[str]:
        if not self.tdx_client_id or not self.tdx_client_secret:
            diag_logs.append("tdx_auth:NO_CREDENTIALS")
            return None
        now_ts = time.time()
        if self._tdx_token_cache["token"] and now_ts < self._tdx_token_cache["expires_at"] - 60:
            return self._tdx_token_cache["token"]
        auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        try:
            resp = requests.post(
                auth_url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.tdx_client_id,
                    "client_secret": self.tdx_client_secret
                },
                timeout=6
            )
            diag_logs.append(f"tdx_auth:{resp.status_code}")
            if resp.status_code == 200:
                tok_data = resp.json()
                token = tok_data.get("access_token")
                expires_in = int(tok_data.get("expires_in", 86400))
                if token:
                    self._tdx_token_cache = {"token": token, "expires_at": now_ts + expires_in}
                    return token
        except Exception as e:
            diag_logs.append(f"tdx_auth:ERR({type(e).__name__})")
        return None

    def _parse_ais_vessel_records(self, records: list, source_label: str) -> Optional[dict]:
        wufu_rec = None
        island_fleet = []
        wushi_fleet = []
        for item in records:
            if not isinstance(item, dict):
                continue
            lat_raw = item.get("Lat") if "Lat" in item else item.get("lat")
            lon_raw = item.get("Lon") if "Lon" in item else item.get("lon")
            if lat_raw is None or lon_raw is None:
                pos_obj = item.get("Position") or item.get("VesselPosition") or {}
                lat_raw = pos_obj.get("PositionLat") or pos_obj.get("Lat") or pos_obj.get("lat")
                lon_raw = pos_obj.get("PositionLon") or pos_obj.get("Lon") or pos_obj.get("lon")
            if lat_raw is None or lon_raw is None:
                continue
            try:
                lat_v, lon_v = float(lat_raw), float(lon_raw)
            except Exception:
                continue

            if not (24.78 <= lat_v <= 24.92 and 121.80 <= lon_v <= 122.00):
                continue

            mmsi = str(item.get("MMSI") or item.get("mmsi") or "").strip()
            sog = float(item.get("SOG") or item.get("sog") or item.get("Speed") or item.get("speed") or 0.0)
            cog = item.get("COG") if "COG" in item else item.get("cog")
            vessel_name = str(item.get("VesselName") or item.get("ShipName") or item.get("name") or "").strip()

            d_island = min(
                self._haversine_distance(lat_v, lon_v, self.pier_north["lat"], self.pier_north["lon"]),
                self._haversine_distance(lat_v, lon_v, self.pier_south["lat"], self.pier_south["lon"])
            )
            d_wushi = self._haversine_distance(lat_v, lon_v, self.pier_wushi["lat"], self.pier_wushi["lon"])

            if d_island <= 850.0:
                island_fleet.append({"mmsi": mmsi, "name": vessel_name, "sog": sog, "dist_m": round(d_island, 1)})
            if d_wushi <= 1200.0:
                wushi_fleet.append({"mmsi": mmsi, "name": vessel_name, "sog": sog})

            if mmsi == "416017708" or "五福" in vessel_name:
                wufu_rec = {
                    "lat": lat_v, "lon": lon_v, "sog": sog, "cog": cog,
                    "source_tag": source_label, "match_type": "DIRECT_MMSI_416017708"
                }

        if wufu_rec:
            wufu_rec["island_fleet_count"] = len(island_fleet)
            wufu_rec["wushi_fleet_count"] = len(wushi_fleet)
            return wufu_rec

        if island_fleet:
            return {
                "lat": self.pier_north["lat"], "lon": self.pier_north["lon"], "sog": 0.2,
                "source_tag": f"{source_label}·賞鯨船隊群集({len(island_fleet)}艘駐島)",
                "match_type": "FLEET_CLUSTER_OPEN",
                "island_fleet_count": len(island_fleet),
                "wushi_fleet_count": len(wushi_fleet)
            }

        if records:
            return {
                "lat": self.pier_wushi["lat"], "lon": self.pier_wushi["lon"], "sog": 0.0,
                "source_tag": f"{source_label}·島周0船(船隊滯港)",
                "match_type": "FLEET_CLUSTER_CLOSED",
                "island_fleet_count": 0,
                "wushi_fleet_count": len(wushi_fleet)
            }
        return None

    def fetch_tdx_ais_realtime(self, diag_logs: list) -> Optional[dict]:
        """通道 1：TDX OAuth2 REST API (v3 / v2 雙版本端點查詢)"""
        token = self._get_tdx_access_token(diag_logs)
        if not token:
            return None

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        spatial_filter = "Lat ge 24.78 and Lat le 24.92 and Lon ge 121.80 and Lon le 122.00"
        tdx_endpoints = [
            "https://tdx.transportdata.tw/api/basic/v3/Maritime/AIS/RealTime?$filter=MMSI eq '416017708'&$format=JSON",
            "https://tdx.transportdata.tw/api/basic/v2/Maritime/AIS/RealTime?$filter=MMSI eq '416017708'&$format=JSON",
            f"https://tdx.transportdata.tw/api/basic/v3/Maritime/AIS/RealTime?$filter={spatial_filter}&$format=JSON",
            f"https://tdx.transportdata.tw/api/basic/v2/Maritime/AIS/RealTime?$filter={spatial_filter}&$format=JSON",
            "https://tdx.transportdata.tw/api/basic/v3/Maritime/AIS/RealTime?$top=300&$format=JSON"
        ]
        for idx, ep in enumerate(tdx_endpoints):
            try:
                resp = requests.get(ep, headers=headers, timeout=6)
                diag_logs.append(f"tdx_ais_{idx+1}:{resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    records = data if isinstance(data, list) else (data.get("AIS") or data.get("data") or data.get("value") or [])
                    parsed = self._parse_ais_vessel_records(records, "TDX_REST即時")
                    if parsed:
                        return parsed
            except Exception as e:
                diag_logs.append(f"tdx_ais_{idx+1}:ERR({type(e).__name__})")
        return None

    def fetch_tdx_mqtt_ais_burst(self, diag_logs: list, listen_sec: float = 3.5) -> Optional[dict]:
        """通道 2：TDX MQTT Broker (mqtt.transportdata.tw:8883 TLS) 短時視窗訂閱備援"""
        if not (self.tdx_mm_id and self.tdx_mm_username and self.tdx_mm_pw):
            diag_logs.append("tdx_mqtt:NO_CREDENTIALS")
            return None
        if not HAS_PAHO_MQTT:
            diag_logs.append("tdx_mqtt:NO_PAHO_LIB")
            return None

        collected_records = []
        conn_state = {"rc": None}

        def on_connect(client, userdata, flags, reason_code, properties=None):
            conn_state["rc"] = str(reason_code)
            if str(reason_code) in ["0", "Success"]:
                for topic in [
                    "TDX/Maritime/AIS/RealTime/#",
                    "v2/Maritime/AIS/RealTime/#",
                    "v3/Maritime/AIS/RealTime/#"
                ]:
                    client.subscribe(topic, qos=0)

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode("utf-8", errors="ignore"))
                if isinstance(payload, list):
                    collected_records.extend(payload)
                elif isinstance(payload, dict):
                    recs = payload.get("AIS") or payload.get("data") or payload.get("value")
                    if isinstance(recs, list):
                        collected_records.extend(recs)
                    else:
                        collected_records.append(payload)
            except Exception:
                pass

        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.tdx_mm_id, protocol=mqtt.MQTTv311)
        except Exception:
            client = mqtt.Client(client_id=self.tdx_mm_id)

        client.username_pw_set(self.tdx_mm_username, self.tdx_mm_pw)
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect("mqtt.transportdata.tw", 8883, keepalive=15)
            client.loop_start()
            deadline = time.time() + listen_sec
            while time.time() < deadline:
                if any(str(r.get("MMSI") or r.get("mmsi") or "") == "416017708" for r in collected_records if isinstance(r, dict)):
                    break
                time.sleep(0.25)
            client.loop_stop()
            client.disconnect()
            diag_logs.append(f"tdx_mqtt:rc={conn_state['rc']},msgs={len(collected_records)}")
        except Exception as e:
            diag_logs.append(f"tdx_mqtt:ERR({type(e).__name__})")
            return None

        if collected_records:
            return self._parse_ais_vessel_records(collected_records, "TDX_MQTT即時推播")
        return None

    def fetch_realtime_ais_api(self, diag_logs: list) -> Optional[dict]:
        tdx_res = self.fetch_tdx_ais_realtime(diag_logs)
        if tdx_res:
            return tdx_res

        mqtt_res = self.fetch_tdx_mqtt_ais_burst(diag_logs)
        if mqtt_res:
            return mqtt_res

        if not self.ais_api_url:
            diag_logs.append("custom_ais:NO_URL")
            return None
        try:
            resp = requests.get(self.ais_api_url, timeout=4)
            diag_logs.append(f"custom_ais:{resp.status_code}")
            if resp.status_code == 200:
                payload = resp.json()
                records = payload if isinstance(payload, list) else payload.get("data", [payload])
                return self._parse_ais_vessel_records(records, "自訂AIS即時API")
        except Exception as e:
            diag_logs.append(f"custom_ais:ERR({type(e).__name__})")
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

    def analyze_trajectory_vector(self, track_history: List[dict], is_real_ais: bool, ais_diag: List[str] = None) -> Dict[str, Any]:
        ais_diag = ais_diag or []
        if not is_real_ais:
            has_rest = bool(self.tdx_client_id and self.tdx_client_secret)
            has_mqtt = bool(self.tdx_mm_id and self.tdx_mm_username and self.tdx_mm_pw)
            if not has_rest and not has_mqtt:
                desc = "🛰️ 未設定TDX(REST/MQTT)金鑰 (水文推演備援)"
            elif any("tdx_auth:200" in d or "tdx_mqtt:rc=0" in d or "tdx_mqtt:rc=Success" in d for d in ais_diag):
                desc = "📡 TDX雙通道已連線·海域暫無AIS回傳 (水文推演備援)"
            else:
                desc = f"⚠️ TDX認證/連線異常 ({','.join(ais_diag[:3])}) · 水文推演備援"
            return {"vector_state": "HYDRO_FALLBACK", "vector_desc": desc, "delta_dist_m": 0.0, "cog_deg": None}

        if len(track_history) < 2:
            return {"vector_state": "INITIAL_POINT", "vector_desc": "📡 TDX/AIS首筆定位建立中 (待累積軌跡)", "delta_dist_m": 0.0, "cog_deg": None}

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
            state, desc = "STATIONARY_AT_PIER", "🟢 軌跡穩定駐泊碼頭戒護 (Δd≈0m)"
        elif delta_d > 300.0 and sog >= 3.0 and (cog is not None and 235.0 <= cog <= 320.0):
            state, desc = "RETREATING_TO_WUSHI", f"🔴 軌跡返航烏石港 (COG {cog}°, Δd=+{delta_d}m) [早退/封島鐵證]"
        elif delta_d < -300.0 and sog >= 3.0 and (cog is not None and 80.0 <= cog <= 140.0):
            state, desc = "APPROACHING_ISLAND", f"🚢 軌跡駛向龜山島 (COG {cog}°, Δd={delta_d}m) [準備開島]"
        elif 200.0 < d_curr <= 1000.0 and sog > 2.0 and abs(delta_d) < 150.0:
            state, desc = "LOITERING_FAILED_DOCK", f"⚠️ 島周繞行無法靠泊 (距岸 {round(d_curr)}m, SOG {sog}kt)"
        else:
            state, desc = "BERTHED_OR_IDLE", f"⚓ 靜止待命 (距島 {round(d_curr)}m, Δd={delta_d}m)"

        return {"vector_state": state, "vector_desc": desc, "delta_dist_m": delta_d, "cog_deg": cog}

    def _infer_vessel_position_from_hydrodynamics(self, telemetry: dict, dt: datetime) -> dict:
        hs = float(telemetry.get("hs", 1.15))
        tp = float(telemetry.get("tp", 8.5))
        w = float(telemetry.get("w", 5.5))
        theta = float(telemetry.get("monsoon_angle", 35.0))
        ann = telemetry.get("official_announcement", {})
        web_veto = int(ann.get("official_veto", 0)) == 1
        south_closed = bool(ann.get("south_pier_closed_damage", True))

        kd_n = 1.00 if tp >= 12.0 else 0.883
        kd_s = 1.00 if tp >= 12.0 else 0.72
        hs_n, hs_s = hs * kd_n, hs * kd_s
        kw = 0.78 if theta < 35.0 else (0.88 if theta < 45.0 else 1.00)
        weff = w * abs(math.cos(math.radians(theta))) * kw

        if not web_veto and self.is_operational_boat_hours(dt):
            if hs_n <= 0.95 and weff <= 8.50:
                return {"lat": 24.84375, "lon": 121.94378, "sog": 0.1, "source_tag": "水文推演備援·北岸"}
            elif not south_closed and hs_s <= 1.13 and weff <= 10.17:
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
            state_desc, dock_code, implied_open = f"🟢 五福號靠泊北岸戒護中 ({source_tag})", "DOCKED_NORTH", True
        elif is_docked_south:
            state_desc, dock_code, implied_open = f"🟡 五福號靠泊南岸戒護中 ({source_tag})", "DOCKED_SOUTH", True
        elif dist_wushi <= 1200.0 and sog <= 0.8:
            if in_boat_hours:
                state_desc, dock_code = f"🔴 五福號船班時段停泊烏石港未出港 ({source_tag})", "BERTHED_WUSHI_CLOSED"
            else:
                state_desc, dock_code = f"🌙 五福號非營運時段停泊烏石港母港 ({source_tag})", "BERTHED_WUSHI_OFFHOURS"
            implied_open = False
        elif dist_north <= 900.0 or dist_south <= 900.0:
            state_desc, dock_code, implied_open = f"⚠️ 五福號島周繞行無法靠泊 ({source_tag})", "PATROLLING_FAILED", False
        else:
            state_desc, dock_code, implied_open = f"🚢 五福號航道往返航行中 ({source_tag})", "EN_ROUTE", False

        return {
            "lat": round(off_lat, 6), "lon": round(off_lon, 6),
            "dist_wushi_m": round(dist_wushi, 1), "dist_north_m": round(dist_north, 1), "dist_south_m": round(dist_south, 1),
            "is_real_ais": is_real_ais, "is_docked_island": is_docked_island, "in_boat_hours": in_boat_hours,
            "implied_official_open": implied_open, "dock_code": dock_code, "dock_desc": state_desc
        }

    def track_and_back_calculate(self, telemetry: dict, dt: datetime = None) -> dict:
        dt = dt or datetime.now(CST)
        off = self.official_vessel
        fleet_cnt = 0
        ais_diag = []
        if "wufu_lat" in telemetry and "wufu_lon" in telemetry:
            lat, lon, sog, tag, is_real_ais = float(telemetry["wufu_lat"]), float(telemetry["wufu_lon"]), float(telemetry.get("wufu_sog", 0.2)), "AIS即時傳入", True
            ais_diag.append("direct_telemetry_ais:OK")
        else:
            live_ais = self.fetch_realtime_ais_api(ais_diag)
            if live_ais:
                lat, lon, sog, tag, is_real_ais = live_ais["lat"], live_ais["lon"], live_ais["sog"], live_ais["source_tag"], True
                fleet_cnt = live_ais.get("island_fleet_count", 0)
            else:
                inferred = self._infer_vessel_position_from_hydrodynamics(telemetry, dt)
                lat, lon, sog, tag, is_real_ais = inferred["lat"], inferred["lon"], inferred["sog"], inferred["source_tag"], False

        track_history = self._update_and_load_track(lat, lon, sog, tag, is_real_ais, dt)
        traj_eval = self.analyze_trajectory_vector(track_history, is_real_ais, ais_diag)
        dock_eval = self.evaluate_docking_status(lat, lon, sog, tag, is_real_ais, dt)

        return {
            "official_wufu": {
                "name": off["name"], "mmsi": off["mmsi"],
                "coord_str": f"{lat:.5f}° N, {lon:.5f}° E", "sog_knots": sog,
                "island_fleet_count": fleet_cnt,
                "ais_diagnostics": ais_diag,
                **dock_eval, **traj_eval
            },
            "wushi_port_fleet_flux": {"v_flux_ships_per_hour": 42.0 if dock_eval["implied_official_open"] else 0.0}
        }
