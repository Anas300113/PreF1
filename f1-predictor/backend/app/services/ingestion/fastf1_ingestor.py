from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.fastf1_client import FastF1Client
from app.models import Lap, TyreStint, WeatherObservation
from app.utils.logging_config import get_logger

logger = get_logger("fastf1_ingestor")

class FastF1Ingestor:
    def __init__(self, db_session: AsyncSession, client: FastF1Client):
        self.db = db_session
        self.client = client

    async def ingest_session_laps(
        self, race_id: str, year: int, round_num: int, session_type: str = "R"
    ) -> int:
        session = self.client.get_session(year, round_num, session_type)
        if session is None:
            return 0

        laps_df = self.client.get_laps_dataframe(session, pick_quicklaps=False, exclude_sc_laps=False)
        if laps_df.empty:
            return 0

        count = 0
        s_type_map = {"R": "race", "Q": "qualifying", "FP1": "fp1", "FP2": "fp2", "FP3": "fp3"}
        normalized_stype = s_type_map.get(session_type.upper(), session_type.lower())

        for _, row in laps_df.iterrows():
            driver_code = str(row.get("Driver", ""))
            lap_num = int(row.get("LapNumber", 0))

            if not driver_code or lap_num <= 0:
                continue

            # Driver mapping lookup could be added, here we store driver_code as driver_id or map
            stmt = select(Lap).where(
                Lap.race_id == race_id,
                Lap.driver_id == driver_code,
                Lap.lap_number == lap_num,
                Lap.session_type == normalized_stype
            )
            existing = (await self.db.execute(stmt)).scalar_one_or_none()

            lap_time = float(row["LapTime"]) if pd_not_na(row.get("LapTime")) else None
            s1 = float(row["Sector1Time"]) if pd_not_na(row.get("Sector1Time")) else None
            s2 = float(row["Sector2Time"]) if pd_not_na(row.get("Sector2Time")) else None
            s3 = float(row["Sector3Time"]) if pd_not_na(row.get("Sector3Time")) else None

            if existing:
                existing.lap_time_s = lap_time
                existing.sector1_s = s1
                existing.sector2_s = s2
                existing.sector3_s = s3
            else:
                lap = Lap(
                    race_id=race_id,
                    driver_id=driver_code,
                    lap_number=lap_num,
                    session_type=normalized_stype,
                    lap_time_s=lap_time,
                    sector1_s=s1,
                    sector2_s=s2,
                    sector3_s=s3,
                    compound=str(row.get("Compound")) if pd_not_na(row.get("Compound")) else None,
                    tyre_life=int(row.get("TyreLife")) if pd_not_na(row.get("TyreLife")) else None,
                    stint_number=int(row.get("Stint")) if pd_not_na(row.get("Stint")) else None,
                    track_status=str(row.get("TrackStatus")) if pd_not_na(row.get("TrackStatus")) else None,
                    source="fastf1"
                )
                self.db.add(lap)
            count += 1

        # Also ingest stints if race session
        if normalized_stype == "race":
            stints_df = self.client.get_stints_from_laps(laps_df)
            for _, s_row in stints_df.iterrows():
                stint = TyreStint(
                    race_id=race_id,
                    driver_id=str(s_row["driver_id"]),
                    stint_number=int(s_row["stint_number"]),
                    compound=str(s_row["compound"]),
                    start_lap=int(s_row["start_lap"]),
                    end_lap=int(s_row["end_lap"]),
                    stint_length=int(s_row["stint_length"]),
                    avg_pace_s=float(s_row["avg_pace_s"]),
                    pace_degradation_s_per_lap=float(s_row["pace_degradation_s_per_lap"]),
                    cliff_detected=bool(s_row["cliff_detected"]),
                    source="fastf1"
                )
                self.db.add(stint)

        await self.db.commit()
        logger.info("Ingested FastF1 laps", race_id=race_id, count=count, session=session_type)
        return count

def pd_not_na(val) -> bool:
    import pandas as pd
    return val is not None and pd.notna(val)
