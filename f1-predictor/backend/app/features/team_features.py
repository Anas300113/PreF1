from typing import Dict, Any, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import RaceResult, Race, QualifyingResult
from app.features.driver_features import _race_cutoff_date

class TeamFeatureExtractor:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def compute_rolling_features(self, team_id: str, race_id_cutoff: str) -> Dict[str, Any]:
        # Chronological cutoff by calendar date (race IDs are not lexicographically ordered)
        cutoff_date = await _race_cutoff_date(self.db, race_id_cutoff)
        if cutoff_date is None:
            return {}
        stmt = (
            select(RaceResult, Race.race_date)
            .join(Race, RaceResult.race_id == Race.id)
            .where(RaceResult.team_id == team_id, Race.race_date < cutoff_date)
            .order_by(Race.race_date.desc())
        )
        res = await self.db.execute(stmt)
        rows = res.all()

        dnfs = [1 if r.RaceResult.dnf else 0 for r in rows[:10]]
        team_dnf_5 = float(np.mean(dnfs[:5])) if dnfs else np.nan

        # Team quali pace gap
        q_stmt = (
            select(QualifyingResult.gap_to_pole_s)
            .join(Race, QualifyingResult.race_id == Race.id)
            .where(QualifyingResult.team_id == team_id, Race.race_date < cutoff_date)
            .order_by(Race.race_date.desc())
            .limit(10)
        )
        q_res = await self.db.execute(q_stmt)
        q_gaps = [g for g in q_res.scalars().all() if g is not None]
        team_quali_pace = float(np.mean(q_gaps)) if q_gaps else np.nan

        return {
            "team_quali_pace_vs_field": team_quali_pace,
            "team_dnf_rate_5": team_dnf_5,
        }

    async def get_all_features(self, team_id: str, race_id_cutoff: str) -> Dict[str, Any]:
        return await self.compute_rolling_features(team_id, race_id_cutoff)
