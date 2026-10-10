#!/usr/bin/env python3
"""Seed a PostgreSQL deployment from the local SQLite development database.

Serverless hosting (e.g. Vercel) gives functions a read-only filesystem and no
persistent volume, so the checked-out SQLite file cannot be written to and its
contents would not survive between invocations. The supported production path is
therefore a managed Postgres instance pointed at by DATABASE_URL, hydrated once
from the local database by this script.

Run this locally (where the filesystem is writable) BEFORE deploying:

    python scripts/seed_postgres.py --to "$DATABASE_URL"

The script creates the schema with create_all() and then upserts every row using
Postgres' on-conflict clause, so it is idempotent: re-running it re-syncs rather
than duplicating. Tables are copied in FK-dependency order. Rows are streamed in
batches so memory stays bounded on large tables.

Pass --truncate to clear destination tables first (destructive).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import Base
import app.models  # noqa: F401  (registers every ORM table on Base.metadata)
from app.utils.logging_config import setup_logging

setup_logging("INFO")

# Parents before children so foreign keys resolve on insert.
ORDER = [
    "seasons",
    "circuits",
    "drivers",
    "teams",
    "driver_team_seasons",
    "races",
    "race_entries",
    "race_results",
    "qualifying_results",
    "pit_stops",
    "laps",
    "tyre_stints",
    "weather_observations",
    "driver_form_snapshots",
    "team_form_snapshots",
    "championship_standings",
    "dataset_provenance",
    "predictions",
    "prediction_driver_results",
    "simulation_runs",
    "backtest_seasons",
    "backtest_races",
]

BATCH = 500

def _sync_url(url: str) -> str:
    """Strip async drivers so a plain sync engine can read the source."""
    return url.replace("+aiosqlite", "").replace("+asyncpg", "")


async def seed(from_url: str, to_url: str, truncate: bool) -> int:
    src_engine = create_engine(_sync_url(from_url))
    src_meta = MetaData()

    with src_engine.connect() as conn:
        src_tables = set(inspect(conn).get_table_names())

    if not src_tables:
        raise SystemExit(f"No tables found in source database: {from_url}")

    src_meta.reflect(bind=src_engine, only=sorted(src_tables))

    dst_engine = create_async_engine(to_url)
    total = 0
    try:
        async with dst_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            dst_names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
            if truncate:
                for name in reversed(ORDER + sorted(src_tables - set(ORDER))):
                    if name in dst_names:
                        await conn.execute(text(f'TRUNCATE TABLE "{name}" CASCADE'))

            ordered = [t for t in ORDER if t in src_tables]
            ordered += sorted(src_tables - set(ORDER))

            with src_engine.connect() as sconn:
                for name in ordered:
                    if name not in dst_names:
                        print(f"  skip {name}: absent from destination schema")
                        continue

                    table = src_meta.tables[name]
                    pks = [c.name for c in table.primary_key.columns]
                    if not pks:
                        print(f"  skip {name}: no primary key, cannot upsert")
                        continue

                    target = Table(name, Base.metadata)
                    updatable = {
                        c.name: pg_insert(target).excluded[c.name]
                        for c in target.columns
                        if c.name not in pks
                    }

                    copied = 0
                    result = sconn.execute(select(table))
                    while True:
                        chunk = result.fetchmany(BATCH)
                        if not chunk:
                            break
                        payload = [dict(r._mapping) for r in chunk]
                        stmt = pg_insert(target).values(payload)
                        if updatable:
                            stmt = stmt.on_conflict_do_update(
                                index_elements=pks, set_=updatable
                            )
                        else:
                            stmt = stmt.on_conflict_do_nothing(index_elements=pks)
                        await conn.execute(stmt)
                        copied += len(payload)

                    if copied:
                        print(f"  {name:28} {copied:>8,} rows")
                        total += copied
    finally:
        await dst_engine.dispose()
        src_engine.dispose()
    return total


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--from",
        dest="src",
        default="sqlite+aiosqlite:///./data/db/f1_predictor.db",
        help="source SQLAlchemy URL (default: local dev SQLite)",
    )
    ap.add_argument(
        "--to", dest="dst", required=True, help="destination PostgreSQL URL"
    )
    ap.add_argument(
        "--truncate",
        action="store_true",
        help="TRUNCATE destination tables before seeding (destructive)",
    )
    args = ap.parse_args()

    if "postgres" not in args.dst:
        raise SystemExit(
            "--to must be a PostgreSQL URL (e.g. postgresql+asyncpg://user:pw@host/db)"
        )

    print(f"Seeding Postgres from {args.src} ...")
    total = await seed(args.src, args.dst, args.truncate)
    print(f"Done. {total:,} rows seeded.")


if __name__ == "__main__":
    asyncio.run(main())

