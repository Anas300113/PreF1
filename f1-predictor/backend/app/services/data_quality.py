from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import RaceResult, Lap, QualifyingResult

class DataQualityChecker:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def check_duplicate_race_results(self, race_id: str) -> List[str]:
        stmt = (
            select(RaceResult.driver_id, func.count(RaceResult.id))
            .where(RaceResult.race_id == race_id)
            .group_by(RaceResult.driver_id)
            .having(func.count(RaceResult.id) > 1)
        )
        res = await self.db.execute(stmt)
        duplicates = res.all()
        return [f"Duplicate race result for driver {driver_id}" for driver_id, _ in duplicates]

    async def check_impossible_lap_times(
        self, race_id: str, min_seconds: float = 50.0, max_seconds: float = 300.0
    ) -> List[str]:
        stmt = select(Lap).where(
            Lap.race_id == race_id,
            ((Lap.lap_time_s < min_seconds) | (Lap.lap_time_s > max_seconds))
        )
        res = await self.db.execute(stmt)
        bad_laps = res.scalars().all()
        return [f"Impossible lap time {lap.lap_time_s}s for driver {lap.driver_id} on lap {lap.lap_number}" for lap in bad_laps]

    async def check_position_uniqueness(self, race_id: str) -> List[str]:
        stmt = (
            select(RaceResult.finish_position, func.count(RaceResult.id))
            .where(RaceResult.race_id == race_id, RaceResult.finish_position.isnot(None))
            .group_by(RaceResult.finish_position)
            .having(func.count(RaceResult.id) > 1)
        )
        res = await self.db.execute(stmt)
        dups = res.all()
        return [f"Duplicate finishing position {pos}" for pos, _ in dups]

    async def run_all_checks(self, race_id: str) -> Dict[str, List[str]]:
        dup_res = await self.check_duplicate_race_results(race_id)
        lap_res = await self.check_impossible_lap_times(race_id)
        pos_res = await self.check_position_uniqueness(race_id)

        return {
            "duplicate_results": dup_res,
            "impossible_laps": lap_res,
            "duplicate_positions": pos_res,
        }
