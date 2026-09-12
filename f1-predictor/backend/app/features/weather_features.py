from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import WeatherObservation, Race

class WeatherFeatureExtractor:
    """Leakage-safe weather features.

    Only observations recorded strictly BEFORE race day may be used as model
    input: pre-race (e.g. Friday/Saturday) conditions were genuinely known
    before the race, whereas observed race-day weather would leak the outcome.
    """
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_race_weather_features(self, race_id: str) -> Dict[str, Any]:
        stmt = (
            select(WeatherObservation, Race.race_date)
            .join(Race, WeatherObservation.race_id == Race.id)
            .where(WeatherObservation.race_id == race_id)
            .order_by(WeatherObservation.observed_at.desc())
        )
        res = await self.db.execute(stmt)
        race_date = (await self.db.execute(
            select(Race.race_date).where(Race.id == race_id)
        )).scalar_one_or_none()

        obs = None
        for candidate, _ in res.all():
            # Strictly pre-race-day observations only (no race-day leakage)
            if race_date is None or candidate.observed_at.date() < race_date:
                obs = candidate
                break

        if not obs:
            return {
                "weather_is_wet": False,
                "weather_race_temp_c": 22.0,
            }

        return {
            "weather_is_wet": bool(obs.is_wet),
            "weather_race_temp_c": float(obs.temperature_c) if obs.temperature_c is not None else 22.0,
        }
