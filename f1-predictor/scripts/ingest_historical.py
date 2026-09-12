#!/usr/bin/env python3
"""CLI script to ingest historical F1 data from Jolpica into SQLite."""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import AsyncSessionLocal, init_db
from app.services.jolpica_client import JolpicaClient
from app.services.ingestion.jolpica_ingestor import JolpicaIngestor
from app.utils.logging_config import setup_logging

setup_logging("INFO")


async def ingest_driver_lineups(ingestor: JolpicaIngestor, year: int) -> None:
    """Populate driver_team_seasons from championship standings."""
    client = ingestor.client
    standings = await client.get_driver_standings(year)
    for entry in standings:
        d_info = entry.get("Driver", {})
        c_info = entry.get("Constructors", [{}])[0] if entry.get("Constructors") else {}
        if not d_info.get("driverId") or not c_info.get("constructorId"):
            continue
        await ingestor._ensure_driver(d_info)
        await ingestor._ensure_team(c_info)
        from sqlalchemy import select
        from app.models import DriverTeamSeason

        stmt = select(DriverTeamSeason).where(
            DriverTeamSeason.driver_id == d_info["driverId"],
            DriverTeamSeason.season_year == year,
        )
        if not (await ingestor.db.execute(stmt)).scalar_one_or_none():
            ingestor.db.add(DriverTeamSeason(
                driver_id=d_info["driverId"],
                team_id=c_info["constructorId"],
                season_year=year,
            ))
    await ingestor.db.commit()


async def main(start_year: int, end_year: int):
    print(f"Starting PreF1 ingestion ({start_year}–{end_year})...")
    await init_db()

    client = JolpicaClient()
    async with AsyncSessionLocal() as session:
        ingestor = JolpicaIngestor(session, client)
        await ingestor.ingest_circuits()
        await ingestor.ingest_seasons(start_year, end_year)

        for year in range(start_year, end_year + 1):
            print(f"Ingesting season {year}...")
            await ingest_driver_lineups(ingestor, year)
            summary = await ingestor.ingest_full_season(year)
            print(f"  {year}: {summary}")

    await client.close()
    print("Ingestion completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest F1 historical data from Jolpica")
    parser.add_argument("--start", type=int, default=2018, help="First season year")
    parser.add_argument("--end", type=int, default=2025, help="Last season year")
    args = parser.parse_args()
    asyncio.run(main(args.start, args.end))
