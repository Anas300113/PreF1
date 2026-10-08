from typing import Optional, Dict, Any, List
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import RaceResult, Race, QualifyingResult


async def _race_cutoff_date(db: AsyncSession, race_id_cutoff: str):
    """Resolve the calendar date of the cutoff race.

    Race IDs are lexicographic strings ("2024_10" < "2024_9"), so they must
    never be used for chronological filtering. Use race_date instead.
    """
    stmt = select(Race.race_date).where(Race.id == race_id_cutoff)
    return (await db.execute(stmt)).scalar_one_or_none()


class DriverFeatureExtractor:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    @staticmethod
    def recency_weighted(values: list, half_life: int = 5) -> float:
        """Exponential-decay weighted average with configurable half-life.

        Recent races matter more than distant history (recency weighting).
        half_life=5 means the weight halves every 5 races back.
        """
        if not values:
            return np.nan
        weights = [2 ** (-i / half_life) for i in range(len(values))]
        total_w = sum(weights)
        return sum(v * w for v, w in zip(values, weights)) / total_w

    async def compute_rolling_features(
        self, driver_id: str, race_id_cutoff: str, circuit_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # Fetch race results strictly BEFORE the cutoff race's calendar date.
        cutoff_date = await _race_cutoff_date(self.db, race_id_cutoff)
        if cutoff_date is None:
            return {}
        stmt = (
            select(RaceResult, Race.race_date, Race.circuit_id)
            .join(Race, RaceResult.race_id == Race.id)
            .where(RaceResult.driver_id == driver_id, Race.race_date < cutoff_date)
            .order_by(Race.race_date.desc())
        )
        res = await self.db.execute(stmt)
        rows = res.all()

        finishes = [r.RaceResult.finish_position for r in rows if r.RaceResult.finish_position is not None]
        dnfs = [1 if r.RaceResult.dnf else 0 for r in rows]

        r3_finish = float(np.mean(finishes[:3])) if len(finishes) >= 1 else np.nan
        r5_finish = float(np.mean(finishes[:5])) if len(finishes) >= 1 else np.nan
        r10_finish = float(np.mean(finishes[:10])) if len(finishes) >= 1 else np.nan
        r10_finish_recency = self.recency_weighted(finishes[:10])

        dnf_10 = float(np.mean(dnfs[:10])) if len(dnfs) >= 1 else np.nan

        circuit_avg = np.nan
        if circuit_id:
            c_finishes = [
                r.RaceResult.finish_position
                for r in rows
                if r.RaceResult.finish_position is not None and r.circuit_id == circuit_id
            ]
            if c_finishes:
                circuit_avg = float(np.mean(c_finishes))

        return {
            "driver_rolling_3_finish": r3_finish,
            "driver_rolling_5_finish": r5_finish,
            "driver_rolling_10_finish": r10_finish,
            "driver_rolling_10_finish_recency": r10_finish_recency,
            "driver_dnf_rate_10": dnf_10,
            "driver_circuit_avg_finish": circuit_avg,
        }

    async def compute_teammate_relative_features(
        self, driver_id: str, race_id_cutoff: str, n_races: int = 3
    ) -> Dict[str, Any]:
        """Leakage-safe driver-vs-teammate qualifying gaps.

        For every historical event strictly before the cutoff race's calendar
        date where BOTH the driver and a teammate (same team *for that event*)
        have a valid qualifying time, compute:

            driver_best_time - teammate_best_time

        (negative = driver was faster).  Rolling statistics are then taken
        over the most recent valid comparisons only.

        Handles: teammate changes (teammate resolved per-event via the
        qualifying row's team_id), substitutions (any same-team driver with a
        valid time counts), missing qualifying / disqualifications (rows
        without a valid best time are skipped), and sprint qualifying (the
        qualifying_results table only stores the Grand Prix qualifying
        session, sourced from the race qualifying endpoint).
        """
        cutoff_date = await _race_cutoff_date(self.db, race_id_cutoff)
        if cutoff_date is None:
            return {}

        # The driver's own qualifying history before the cutoff, newest first.
        stmt = (
            select(QualifyingResult, Race.race_date)
            .join(Race, QualifyingResult.race_id == Race.id)
            .where(QualifyingResult.driver_id == driver_id, Race.race_date < cutoff_date)
            .order_by(Race.race_date.desc())
        )
        res = await self.db.execute(stmt)
        driver_rows = res.all()
        if not driver_rows:
            return self._teammate_stats([])

        # One query for every event involved — no N+1.
        race_ids = list({row.QualifyingResult.race_id for row in driver_rows})
        tm_stmt = select(QualifyingResult).where(QualifyingResult.race_id.in_(race_ids))
        tm_rows = (await self.db.execute(tm_stmt)).scalars().all()
        by_race: Dict[str, List[QualifyingResult]] = {}
        for q in tm_rows:
            by_race.setdefault(q.race_id, []).append(q)

        gaps: List[float] = []
        for row in driver_rows:
            dq = row.QualifyingResult
            if dq.best_time_s is None:
                continue  # no valid time (DNS / DSQ / missing data)
            # Teammate = same team *for this event*, different driver.
            teammates = [
                t
                for t in by_race.get(dq.race_id, [])
                if t.driver_id != driver_id
                and t.team_id == dq.team_id
                and t.best_time_s is not None
            ]
            if not teammates:
                continue  # teammate change with no same-event comparison, or missing data
            teammate_time = float(np.mean([t.best_time_s for t in teammates]))
            gaps.append(float(dq.best_time_s) - teammate_time)

        return self._teammate_stats(gaps, n_races=n_races)

    @staticmethod
    def _teammate_stats(gaps: List[float], n_races: int = 3) -> Dict[str, Any]:
        """Rolling statistics over newest-first teammate gap list."""
        g_n = gaps[:n_races]
        g5 = gaps[:5]
        if not gaps:
            return {
                "driver_quali_vs_teammate_3": np.nan,
                "driver_quali_vs_teammate_5_mean": np.nan,
                "driver_quali_vs_teammate_5_median": np.nan,
                "driver_quali_vs_teammate_5_std": np.nan,
                "driver_teammate_q_h2h_win_rate": np.nan,
                "driver_teammate_q_comparisons": 0.0,
            }
        return {
            # Negative = faster than teammate.  Primary model feature kept
            # under its historical name for schema compatibility.
            "driver_quali_vs_teammate_3": float(np.mean(g_n)) if g_n else np.nan,
            "driver_quali_vs_teammate_5_mean": float(np.mean(g5)),
            "driver_quali_vs_teammate_5_median": float(np.median(g5)),
            "driver_quali_vs_teammate_5_std": float(np.std(g5)) if len(g5) > 1 else 0.0,
            "driver_teammate_q_h2h_win_rate": float(np.mean([1.0 if g < 0 else 0.0 for g in g5])),
            "driver_teammate_q_comparisons": float(len(gaps)),
        }

    @staticmethod
    def _regulation_era_features(race_id_cutoff: str) -> Dict[str, float]:
        """Regulation-era indicator features (F1 regulations change significantly).

        Era boundaries:
          2017-2021: wide cars, high-downforce ground-effect return
          2022+: ground-effect floor, 18-inch wheels, simplified aero
        Data from older eras has weaker predictive power for current seasons.
        """
        try:
            year = int(race_id_cutoff.split("_")[0])
        except (IndexError, ValueError):
            year = 2024
        return {
            "regulation_era_2022_plus": 1.0 if year >= 2022 else 0.0,
            "regulation_era_2017_plus": 1.0 if year >= 2017 else 0.0,
            "season_year": float(year),
        }

    async def get_all_features(
        self, driver_id: str, race_id_cutoff: str, circuit_id: Optional[str] = None
    ) -> Dict[str, Any]:
        rolling = await self.compute_rolling_features(driver_id, race_id_cutoff, circuit_id)
        teammate = await self.compute_teammate_relative_features(driver_id, race_id_cutoff)
        era = self._regulation_era_features(race_id_cutoff)
        return {**rolling, **teammate, **era}
