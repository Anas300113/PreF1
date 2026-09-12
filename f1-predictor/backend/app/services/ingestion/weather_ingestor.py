from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.weather_client import OpenMeteoClient
from app.models import WeatherObservation
from app.utils.logging_config import get_logger

logger = get_logger("weather_ingestor")

class WeatherIngestor:
    def __init__(self, db_session: AsyncSession, client: OpenMeteoClient):
        self.db = db_session
        self.client = client

    async def ingest_race_forecast(
        self, race_id: str, circuit_lat: float, circuit_lon: float, race_date: date
    ) -> int:
        obs_list = await self.client.get_forecast(circuit_lat, circuit_lon, race_date, race_date)
        return await self._save_observations(race_id, obs_list)

    async def ingest_race_historical(
        self,
        race_id: str,
        circuit_lat: float,
        circuit_lon: float,
        start_date: date,
        end_date: date | None = None,
        source_override: str | None = None,
    ) -> int:
        """Ingest archive (observed) weather for a date range.

        ``source_override`` lets callers label the provenance explicitly
        (e.g. "open_meteo_archive_pre_race") so leakage-safe pre-race data is
        distinguishable from observed race-day data.
        """
        end = end_date or start_date
        obs_list = await self.client.get_historical(circuit_lat, circuit_lon, start_date, end)
        if source_override:
            for obs in obs_list:
                obs["source"] = source_override
        return await self._save_observations(race_id, obs_list)

    async def _save_observations(self, race_id: str, obs_list: list[dict]) -> int:
        count = 0
        for obs in obs_list:
            dt = datetime.fromisoformat(obs["observed_at"])
            retrieved_dt = datetime.fromisoformat(obs["source_retrieved_at"])

            wo = WeatherObservation(
                race_id=race_id,
                session_type="race",
                observed_at=dt,
                source=obs["source"],
                source_retrieved_at=retrieved_dt,
                temperature_c=obs["temperature_c"],
                feels_like_c=obs["feels_like_c"],
                humidity_pct=obs["humidity_pct"],
                pressure_hpa=obs["pressure_hpa"],
                precipitation_mm=obs["precipitation_mm"],
                precipitation_probability=obs["precipitation_probability"],
                wind_speed_ms=obs["wind_speed_ms"],
                wind_gust_ms=obs["wind_gust_ms"],
                wind_direction_deg=obs["wind_direction_deg"],
                cloud_cover_pct=obs["cloud_cover_pct"],
                weather_code=obs["weather_code"],
                is_wet=obs["is_wet"],
            )
            self.db.add(wo)
            count += 1

        await self.db.commit()
        logger.info("Ingested weather observations", race_id=race_id, count=count)
        return count
