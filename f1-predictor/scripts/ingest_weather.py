#!/usr/bin/env python3
"""Ingest leakage-safe historical weather for completed races.

For every completed race we fetch Open-Meteo archive data for the PRE-RACE
window only (Friday/Saturday before the race). Those conditions were genuinely
known before the race, so they are legitimate model inputs. Observed race-day
weather is deliberately NOT ingested for training features (spec §5: never
leak future weather into historical training).

Usage:
    python scripts/ingest_weather.py [--start 2018] [--end 2026]
"""
import argparse
import asyncio
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.models import Circuit, Race, WeatherObservation
from app.services.weather_client import OpenMeteoClient
from app.services.ingestion.weather_ingestor import WeatherIngestor
from app.utils.logging_config import setup_logging

setup_logging("INFO")

PRE_RACE_SOURCE = "open_meteo_archive_pre_race"


async def main(start_year: int, end_year: int) -> None:
    print(f"Ingesting pre-race weather ({start_year}–{end_year}) from Open-Meteo archive...")
    await init_db()

    client = OpenMeteoClient()
    total = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Race, Circuit)
            .join(Circuit, Race.circuit_id == Circuit.id)
            .where(
                Race.season_year >= start_year,
                Race.season_year <= end_year,
                Race.status == "completed",
                Race.race_date.is_not(None),
            )
            .order_by(Race.season_year, Race.round_number)
        )
        rows = (await session.execute(stmt)).all()

        for race, circuit in rows:
            if circuit.latitude is None or circuit.longitude is None:
                skipped += 1
                continue

            existing = (
                await session.execute(
                    select(WeatherObservation)
                    .where(
                        WeatherObservation.race_id == race.id,
                        WeatherObservation.source == PRE_RACE_SOURCE,
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
            if existing is not None:
                skipped += 1
                continue

            ingestor = WeatherIngestor(session, client)
            # Friday/Saturday before race day: information available pre-race.
            start = race.race_date - timedelta(days=2)
            end = race.race_date - timedelta(days=1)
            try:
                count = await ingestor.ingest_race_historical(
                    race.id,
                    circuit.latitude,
                    circuit.longitude,
                    start,
                    end,
                    source_override=PRE_RACE_SOURCE,
                )
                total += count
            except Exception as exc:
                await session.rollback()
                print(f"  WARN {race.id}: {exc}")

    await client.close()
    print(f"Weather ingestion complete: {total} observations, {skipped} races skipped (cached/no coords).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest pre-race historical weather")
    parser.add_argument("--start", type=int, default=2018)
    parser.add_argument("--end", type=int, default=2026)
    args = parser.parse_args()
    asyncio.run(main(args.start, args.end))