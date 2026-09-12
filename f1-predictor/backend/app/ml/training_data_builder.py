"""Build chronological training datasets from ingested historical races."""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.race_feature_builder import RaceFeatureBuilder
from app.models import QualifyingResult, Race, RaceResult


class TrainingDataBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_builder = RaceFeatureBuilder(db)

    async def build_qualifying_dataset(
        self, start_year: int = 2018, end_year: int = 2024
    ) -> tuple[pd.DataFrame, pd.Series]:
        X_rows: list[dict[str, Any]] = []
        y_vals: list[float] = []

        races = await self._completed_races(start_year, end_year)
        for race in races:
            features, _ = await self.feature_builder.build_features(race.id)
            if features.empty:
                continue

            quali_stmt = select(QualifyingResult).where(QualifyingResult.race_id == race.id)
            quali = {q.driver_id: q for q in (await self.db.execute(quali_stmt)).scalars().all()}

            for _, row in features.iterrows():
                q = quali.get(row["driver_id"])
                if not q or q.gap_to_pole_s is None:
                    continue
                X_rows.append(row.to_dict())
                y_vals.append(float(q.gap_to_pole_s))

        if not X_rows:
            return pd.DataFrame(), pd.Series(dtype=float)
        return pd.DataFrame(X_rows), pd.Series(y_vals, name="gap_to_pole_s")

    async def build_race_pace_dataset(
        self, start_year: int = 2018, end_year: int = 2024
    ) -> tuple[pd.DataFrame, pd.Series]:
        X_rows: list[dict[str, Any]] = []
        y_vals: list[float] = []

        races = await self._completed_races(start_year, end_year)
        for race in races:
            features, _ = await self.feature_builder.build_features(race.id)
            if features.empty:
                continue

            results_stmt = select(RaceResult).where(RaceResult.race_id == race.id)
            results = {r.driver_id: r for r in (await self.db.execute(results_stmt)).scalars().all()}

            quali_stmt = select(QualifyingResult).where(QualifyingResult.race_id == race.id)
            quali = {q.driver_id: q for q in (await self.db.execute(quali_stmt)).scalars().all()}

            for _, row in features.iterrows():
                rr = results.get(row["driver_id"])
                q = quali.get(row["driver_id"])
                if not rr or rr.finish_position is None:
                    continue
                feat = row.to_dict()
                if q:
                    feat["quali_gap_to_pole"] = q.gap_to_pole_s or feat.get("quali_gap_to_pole", 1.0)
                    feat["quali_position"] = q.position or feat.get("quali_position", 10.0)
                X_rows.append(feat)
                # Normalized race pace proxy: finish position scaled by grid delta
                grid = rr.grid_position or q.position if q else 10
                pace_target = float(rr.finish_position) + 0.1 * (float(grid or 10) - float(rr.finish_position))
                y_vals.append(pace_target)

        if not X_rows:
            return pd.DataFrame(), pd.Series(dtype=float)
        return pd.DataFrame(X_rows), pd.Series(y_vals, name="race_pace_index")

    async def build_dnf_dataset(
        self, start_year: int = 2018, end_year: int = 2024
    ) -> tuple[pd.DataFrame, pd.Series]:
        X_rows: list[dict[str, Any]] = []
        y_vals: list[int] = []

        races = await self._completed_races(start_year, end_year)
        for race in races:
            features, _ = await self.feature_builder.build_features(race.id)
            if features.empty:
                continue

            results_stmt = select(RaceResult).where(RaceResult.race_id == race.id)
            results = {r.driver_id: r for r in (await self.db.execute(results_stmt)).scalars().all()}

            for _, row in features.iterrows():
                rr = results.get(row["driver_id"])
                if not rr:
                    continue
                X_rows.append(row.to_dict())
                y_vals.append(1 if rr.dnf else 0)

        if not X_rows:
            return pd.DataFrame(), pd.Series(dtype=int)
        return pd.DataFrame(X_rows), pd.Series(y_vals, name="dnf")

    async def _completed_races(self, start_year: int, end_year: int) -> list[Race]:
        stmt = (
            select(Race)
            .options(selectinload(Race.circuit))
            .where(
                Race.season_year >= start_year,
                Race.season_year <= end_year,
                Race.status == "completed",
            )
            .order_by(Race.season_year, Race.round_number)
        )
        return list((await self.db.execute(stmt)).scalars().all())


def build_training_datasets_sync(db_url: str, start_year: int = 2018, end_year: int = 2024):
    """Synchronous wrapper for CLI scripts."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(db_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def _run():
        async with Session() as session:
            builder = TrainingDataBuilder(session)
            quali = await builder.build_qualifying_dataset(start_year, end_year)
            pace = await builder.build_race_pace_dataset(start_year, end_year)
            dnf = await builder.build_dnf_dataset(start_year, end_year)
        await engine.dispose()
        return quali, pace, dnf

    return asyncio.run(_run())
