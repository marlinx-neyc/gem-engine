import math
import numpy as np

class GemVesselAgent:
    def __init__(self):
        self.official_vessel = {
            "name": "東北角五福號",
            "mmsi": "416017708",
            "call_sign": "BR5216",
            "kind": "公務小船",
            "draft_m": 1.20,
            "lat": 24.84320,
            "lon": 121.94980
        }
        self.whale_watching_fleet = [
            "華棋168", "北極星1號", "龜山朝日2號", "超級星號",
            "凱鯨號", "東洋銘珠", "新福豐36號", "蘭鯨號", "龜山朝日號"
        ]
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

    def track_and_back_calculate(self, telemetry: dict) -> dict:
        off = self.official_vessel
        dist_wushi = self._haversine_distance(off["lat"], off["lon"], self.pier_wushi["lat"], self.pier_wushi["lon"])
        dist_north = self._haversine_distance(off["lat"], off["lon"], self.pier_north["lat"], self.pier_north["lon"])
        dist_south = self._haversine_distance(off["lat"], off["lon"], self.pier_south["lat"], self.pier_south["lon"])
        return {
            "official_wufu": {
                "name": off["name"],
                "mmsi": off["mmsi"],
                "coord_str": f"{off['lat']:.5f}° N, {off['lon']:.5f}° E",
                "dist_wushi_m": round(dist_wushi, 1),
                "dist_north_m": round(dist_north, 1),
                "dist_south_m": round(dist_south, 1)
            },
            "wushi_port_fleet_flux": {"v_flux_ships_per_hour": 42.0 if telemetry.get("hs", 0) > 1.5 else 7.7}
        }
