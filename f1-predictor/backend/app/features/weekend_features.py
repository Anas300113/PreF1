from typing import Dict, Any
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Lap, QualifyingResult

class WeekendFeatureExtractor:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_practice_features(self, race_id: str, driver_id: str) -> Dict[str, Any]:
        features = {}
        for session_type in ["fp1", "fp2", "fp3"]:
            stmt = (
                select(Lap.lap_time_s)
                .where(
                    Lap.race_id == race_id,
                    Lap.driver_id == driver_id,
                    Lap.session_type == session_type,
                    Lap.deleted == False
                )
            )
            res = await self.db.execute(stmt)
            times = [t for t in res.scalars().all() if t is not None]
            best = min(times) if times else np.nan
            features[f"{session_type}_pace_delta"] = float(best) if not np.isnan(best) else np.nan

        return features

    async def get_qualifying_features(self, race_id: str, driver_id: str) -> Dict[str, Any]:
        stmt = select(QualifyingResult).where(
            QualifyingResult.race_id == race_id,
            QualifyingResult.driver_id == driver_id
        )
        res = await self.db.execute(stmt)
        qr = res.scalar_one_or_none()

        if not qr:
            return {
                "quali_gap_to_pole": np.nan,
                "quali_position": np.nan
            }

        return {
            "quali_gap_to_pole": float(qr.gap_to_pole_s) if qr.gap_to_pole_s is not None else np.nan,
            "quali_position": float(qr.position) if qr.position is not None else np.nan
        }
