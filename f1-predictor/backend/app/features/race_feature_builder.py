"""Build leakage-safe feature matrices for all drivers in a race."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.circuit_features import CircuitFeatureExtractor
from app.features.driver_features import DriverFeatureExtractor
from app.features.team_features import TeamFeatureExtractor
from app.features.weather_features import WeatherFeatureExtractor
from app.models import Driver, DriverTeamSeason, QualifyingResult, Race, Team


DEFAULT_FP_DELTA = 0.0


class RaceFeatureBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.driver_fe = DriverFeatureExtractor(db)
        self.team_fe = TeamFeatureExtractor(db)
        self.circuit_fe = CircuitFeatureExtractor(db)
        self.weather_fe = WeatherFeatureExtractor(db)

    async def get_race_drivers(self, race: Race) -> list[dict[str, Any]]:
        """Drivers entered for this season (from driver_team_seasons)."""
        stmt = (
            select(DriverTeamSeason, Driver, Team)
            .join(Driver, DriverTeamSeason.driver_id == Driver.id)
            .join(Team, DriverTeamSeason.team_id == Team.id)
            .where(DriverTeamSeason.season_year == race.season_year)
        )
        rows = (await self.db.execute(stmt)).all()
        if not rows:
            return []

        return [
            {
                "driver_id": d.id,
                "code": d.code or d.id[:3].upper(),
                "full_name": f"{d.first_name} {d.last_name}".strip(),
                "team_id": t.id,
                "team_name": t.name,
            }
            for _, d, t in rows
        ]

    async def build_features(
        self,
        race_id: str,
        weather_override: dict[str, Any] | None = None,
    ) -> tuple[pd.DataFrame, Race | None]:
        stmt = (
            select(Race)
            .options(selectinload(Race.circuit))
            .where(Race.id == race_id)
        )
        race = (await self.db.execute(stmt)).scalar_one_or_none()
        if not race:
            return pd.DataFrame(), None

        drivers = await self.get_race_drivers(race)
        if not drivers:
            return pd.DataFrame(), race

        circuit_feats = await self.circuit_fe.get_features(race.circuit_id)
        weather_feats = await self.weather_fe.get_race_weather_features(race_id)
        if weather_override:
            weather_feats.update(weather_override)

        # Actual qualifying for this race (if already run) — used as race-pace input only
        quali_stmt = select(QualifyingResult).where(QualifyingResult.race_id == race_id)
        quali_rows = (await self.db.execute(quali_stmt)).scalars().all()
        quali_by_driver = {q.driver_id: q for q in quali_rows}

        rows: list[dict[str, Any]] = []
        for d in drivers:
            driver_id = d["driver_id"]
            team_id = d["team_id"]

            driver_feats = await self.driver_fe.get_all_features(
                driver_id, race_id, race.circuit_id
            )
            team_feats = await self.team_fe.get_all_features(team_id, race_id)

            quali = quali_by_driver.get(driver_id)
            quali_gap = float(quali.gap_to_pole_s) if quali and quali.gap_to_pole_s is not None else np.nan
            quali_pos = int(quali.position) if quali and quali.position else np.nan

            row: dict[str, Any] = {
                "driver_id": driver_id,
                "team_id": team_id,
                "code": d["code"],
                "full_name": d["full_name"],
                "team_name": d["team_name"],
                "race_id": race_id,
                "circuit_id": race.circuit_id,
                "fp1_pace_delta": DEFAULT_FP_DELTA,
                "fp2_pace_delta": DEFAULT_FP_DELTA,
                "fp3_pace_delta": DEFAULT_FP_DELTA,
                "quali_gap_to_pole": quali_gap,
                "quali_position": quali_pos,
                **driver_feats,
                **team_feats,
                **circuit_feats,
                **weather_feats,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df = self._fill_defaults(df)
        return df, race

    @staticmethod
    def _fill_defaults(df: pd.DataFrame) -> pd.DataFrame:
        defaults = {
            "driver_rolling_3_finish": 10.0,
            "driver_rolling_5_finish": 10.0,
            "driver_rolling_10_finish": 10.0,
            "driver_rolling_10_finish_recency": 10.0,
            "driver_dnf_rate_10": 0.08,
            "driver_circuit_avg_finish": 10.0,
            "driver_quali_vs_teammate_3": 0.0,
            "team_quali_pace_vs_field": 0.5,
            "team_dnf_rate_5": 0.08,
            "circuit_length_km": 5.0,
            "circuit_overtaking_difficulty": 0.5,
            "weather_is_wet": False,
            "weather_race_temp_c": 22.0,
            "fp1_pace_delta": 0.0,
            "fp2_pace_delta": 0.0,
            "fp3_pace_delta": 0.0,
            "quali_gap_to_pole": 1.0,
            "quali_position": 10.0,
            "regulation_era_2022_plus": 1.0,
            "regulation_era_2017_plus": 1.0,
            "season_year": 2024.0,
        }
        for col, val in defaults.items():
            if col not in df.columns:
                df[col] = val
            else:
                df[col] = df[col].fillna(val)
        return df
