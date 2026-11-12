import math
from typing import Dict, Any

class GemVesselAgent:
    def __init__(self):
        self.official_vessel = {
            "name": "東北角五福號", "mmsi": "416017708", "call_sign": "BR5216",
            "kind": "公務小船", "draft_m": 1.20,
            "lat": 24.84320, "lon": 121.94980, "sog_knots": 0.2,
            "is_static_baseline": True
        }
        self.pier_wushi = {"lat": 24.86872, "lon": 121.84154}
        self.pier_north = {"lat": 24.843727, "lon": 121.943732}
        self.pier_south = {"lat": 24.840441, "lon": 121.939794}

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return float(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def evaluate_docking_status(self, off_lat: float, off_lon: float, sog: float, is_baseline: bool = True) -> Dict[str, Any]:
        dist_wushi = self._haversine_distance(off_lat, off_lon, self.pier_wushi["lat"], self.pier_wushi["lon"])
        dist_north = self._haversine_distance(off_lat, off_lon, self.pier_north["lat"], self.pier_north["lon"])
        dist_south = self._haversine_distance(off_lat, off_lon, self.pier_south["lat"], self.pier_south["lon"])

        is_docked_north = (dist_north <= 180.0 and sog <= 1.5)
        is_docked_south = (dist_south <= 180.0 and sog <= 1.5)
        is_docked_island = is_docked_north or is_docked_south
        tag = " [AIS基準點]" if is_baseline else ""

        if is_docked_north:
            state_desc = f"🟢 五福號已靠泊北岸碼頭{tag}"
            dock_code = "DOCKED_NORTH"
        elif is_docked_south:
            state_desc = f"🟡 五福號已靠泊南岸碼頭 (機動調撥){tag}"
            dock_code = "DOCKED_SOUTH"
        elif dist_wushi <= 1200.0 and sog <= 0.8:
            state_desc = f"🔴 五福號停泊烏石港母港未出海{tag}"
            dock_code = "BERTHED_WUSHI"
        elif dist_north <= 900.0 or dist_south <= 900.0:
            state_desc = f"⚠️ 五福號島周巡弋未靠泊{tag}"
            dock_code = "PATROLLING_FAILED"
        else:
            state_desc = f"🚢 五福號航道巡察航行中{tag}"
            dock_code = "EN_ROUTE"

        return {
            "dist_wushi_m": round(dist_wushi, 1),
            "dist_north_m": round(dist_north, 1),
            "dist_south_m": round(dist_south, 1),
            "is_docked_island": is_docked_island,
            "dock_code": dock_code,
            "dock_desc": state_desc
        }

    def track_and_back_calculate(self, telemetry: dict) -> dict:
        off = self.official_vessel
        lat = float(telemetry.get("wufu_lat", off["lat"]))
        lon = float(telemetry.get("wufu_lon", off["lon"]))
        sog = float(telemetry.get("wufu_sog", off["sog_knots"]))
        is_base = ("wufu_lat" not in telemetry)
        dock_eval = self.evaluate_docking_status(lat, lon, sog, is_base)
        return {
            "official_wufu": {
                "name": off["name"], "mmsi": off["mmsi"],
                "coord_str": f"{lat:.5f}° N, {lon:.5f}° E",
                "sog_knots": sog,
                **dock_eval
            },
            "wushi_port_fleet_flux": {"v_flux_ships_per_hour": 42.0 if telemetry.get("hs", 0) > 1.5 else 7.7}
        }
