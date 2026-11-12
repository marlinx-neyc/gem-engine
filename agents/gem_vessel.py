import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

CST = timezone(timedelta(hours=8))

class GemVesselAgent:
    def __init__(self):
        self.official_vessel = {
            "name": "東北角五福號", "mmsi": "416017708", "call_sign": "BR5216",
            "kind": "公務小船", "draft_m": 1.20
        }
        self.pier_wushi = {"lat": 24.86872, "lon": 121.84154}
        self.pier_north = {"lat": 24.843727, "lon": 121.943732}
        self.pier_south = {"lat": 24.840441, "lon": 121.939794}

    @staticmethod
    def is_operational_boat_hours(dt: datetime = None) -> bool:
        '''判斷是否處於龜山島日間船班營運時段 (07:00 - 16:30 CST)'''
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

    def _infer_vessel_position_from_hydrodynamics(self, telemetry: dict, dt: datetime) -> dict:
        '''
        當未傳入外部即時 AIS 經緯度時，依據五福號「為登島服務」的作業規律與即時海象反演靠泊態勢：
        - 船班時段內若北岸達標 -> 靠泊北岸碼頭戒護
        - 船班時段內若北岸超標但南岸達標 -> 靠泊南岸碼頭戒護
        - 若全線超標或非船班時段 -> 停泊烏石港母港
        '''
        hs = float(telemetry.get("hs", 1.15))
        tp = float(telemetry.get("tp", 8.5))
        w = float(telemetry.get("w", 5.5))
        theta = float(telemetry.get("monsoon_angle", 35.0))

        kd_n = 1.00 if tp >= 12.0 else (0.75 if theta < 45.0 else 1.00)
        hs_n = hs * kd_n
        hs_s = hs * 0.55
        weff = w * abs(math.cos(math.radians(theta)))

        in_hours = self.is_operational_boat_hours(dt)
        if in_hours:
            if hs_n <= 0.95 and weff <= 8.50:
                return {"lat": 24.84375, "lon": 121.94378, "sog": 0.1, "source_tag": "水文行為反演·北岸駐守"}
            elif hs_s <= 1.13 and weff <= 10.17:
                return {"lat": 24.84048, "lon": 121.93985, "sog": 0.1, "source_tag": "水文行為反演·南岸駐守"}
        return {"lat": 24.86872, "lon": 121.84154, "sog": 0.0, "source_tag": "水文行為反演·母港待命"}

    def evaluate_docking_status(self, off_lat: float, off_lon: float, sog: float, source_tag: str = "AIS即時", dt: datetime = None) -> Dict[str, Any]:
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
            tag = "AIS即時"
        else:
            inferred = self._infer_vessel_position_from_hydrodynamics(telemetry, dt)
            lat, lon, sog, tag = inferred["lat"], inferred["lon"], inferred["sog"], inferred["source_tag"]

        dock_eval = self.evaluate_docking_status(lat, lon, sog, tag, dt)
        return {
            "official_wufu": {
                "name": off["name"], "mmsi": off["mmsi"],
                "coord_str": f"{lat:.5f}° N, {lon:.5f}° E",
                "sog_knots": sog,
                **dock_eval
            },
            "wushi_port_fleet_flux": {"v_flux_ships_per_hour": 42.0 if dock_eval["implied_official_open"] else 0.0}
        }
