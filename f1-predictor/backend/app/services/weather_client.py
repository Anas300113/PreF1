from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from app.utils.logging_config import get_logger
from app.utils.cache import DiskCache

logger = get_logger("weather_client")

class OpenMeteoClient:
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

    HOURLY_VARIABLES = [
        "temperature_2m", "apparent_temperature", "relative_humidity_2m",
        "precipitation", "precipitation_probability", "rain",
        "cloud_cover", "wind_speed_10m", "wind_direction_10m",
        "wind_gusts_10m", "surface_pressure", "weather_code"
    ]

    def __init__(self, cache_dir: str = "./data/cache/weather"):
        self.cache = DiskCache(cache_dir, default_ttl_seconds=21600)  # 6h TTL
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self):
        await self.client.aclose()

    async def get_forecast(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "timezone": "UTC",
        }
        return await self._fetch(self.FORECAST_URL, params, source="open_meteo_forecast")

    async def get_historical(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "timezone": "UTC",
        }
        return await self._fetch(self.ARCHIVE_URL, params, source="open_meteo_archive")

    async def _fetch(self, url: str, params: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        cache_key = f"{url}?{params}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            parsed = self._parse_hourly_response(data, source=source)
            self.cache.set(cache_key, parsed)
            return parsed
        except Exception as e:
            logger.error("Weather fetch failed", url=url, error=str(e))
            return []

    def _parse_hourly_response(self, data: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            return []

        observations = []
        now_str = datetime.now(timezone.utc).isoformat()

        for i, time_str in enumerate(times):
            dt = datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)
            precip = hourly.get("precipitation", [0])[i] or 0.0
            rain = hourly.get("rain", [0])[i] or 0.0
            precip_prob = hourly.get("precipitation_probability", [0])[i] or 0.0

            obs = {
                "observed_at": dt.isoformat(),
                "source": source,
                "source_retrieved_at": now_str,
                "temperature_c": hourly.get("temperature_2m", [None])[i],
                "feels_like_c": hourly.get("apparent_temperature", [None])[i],
                "humidity_pct": hourly.get("relative_humidity_2m", [None])[i],
                "pressure_hpa": hourly.get("surface_pressure", [None])[i],
                "precipitation_mm": precip,
                "precipitation_probability": precip_prob,
                "wind_speed_ms": hourly.get("wind_speed_10m", [None])[i],
                "wind_gust_ms": hourly.get("wind_gusts_10m", [None])[i],
                "wind_direction_deg": hourly.get("wind_direction_10m", [None])[i],
                "cloud_cover_pct": hourly.get("cloud_cover", [None])[i],
                "weather_code": hourly.get("weather_code", [None])[i],
                "is_wet": (precip > 0.5 or rain > 0.3 or precip_prob > 50),
            }
            observations.append(obs)

        return observations
