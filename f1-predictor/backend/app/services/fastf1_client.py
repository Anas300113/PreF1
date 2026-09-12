import os
from typing import Optional
import pandas as pd
import numpy as np
import fastf1
from scipy.stats import linregress
from app.utils.logging_config import get_logger

logger = get_logger("fastf1_client")

class FastF1Client:
    def __init__(self, cache_dir: str = "./data/cache/fastf1"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)

    def get_session(
        self,
        year: int,
        event: str | int,
        session_type: str = "R"
    ) -> Optional[fastf1.core.Session]:
        try:
            session = fastf1.get_session(year, event, session_type)
            session.load(telemetry=False, laps=True, weather=True, messages=False)
            return session
        except Exception as e:
            logger.warning("Failed to load FastF1 session", year=year, event=event, session=session_type, error=str(e))
            return None

    def get_laps_dataframe(
        self,
        session: fastf1.core.Session,
        pick_quicklaps: bool = True,
        exclude_sc_laps: bool = True
    ) -> pd.DataFrame:
        if session is None or session.laps is None or session.laps.empty:
            return pd.DataFrame()
            
        laps = session.laps.copy()
        
        if pick_quicklaps:
            try:
                laps = laps.pick_quicklaps()
            except Exception:
                pass

        if exclude_sc_laps and "TrackStatus" in laps.columns:
            laps = laps[laps["TrackStatus"].astype(str) == "1"]

        # Convert timedelta to float seconds
        time_cols = ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]
        for col in time_cols:
            if col in laps.columns:
                laps[col] = laps[col].dt.total_seconds()
                
        return laps

    def get_weather_dataframe(self, session: fastf1.core.Session) -> pd.DataFrame:
        if session is None or session.weather_data is None or session.weather_data.empty:
            return pd.DataFrame()
            
        df = session.weather_data.copy()
        rename_map = {
            "AirTemp": "temperature_c",
            "TrackTemp": "track_temp_c",
            "Humidity": "humidity_pct",
            "Pressure": "pressure_hpa",
            "WindSpeed": "wind_speed_ms",
            "WindDirection": "wind_direction_deg",
            "Rainfall": "is_wet",
        }
        return df.rename(columns=rename_map)

    def get_stints_from_laps(self, laps_df: pd.DataFrame) -> pd.DataFrame:
        if laps_df.empty or "Stint" not in laps_df.columns:
            return pd.DataFrame()

        stints = []
        grouped = laps_df.groupby(["Driver", "Stint", "Compound"])
        
        for (driver, stint_num, compound), group in grouped:
            clean_laps = group.dropna(subset=["LapTime"])
            if len(clean_laps) < 3:
                continue
                
            start_lap = int(clean_laps["LapNumber"].min())
            end_lap = int(clean_laps["LapNumber"].max())
            stint_length = len(clean_laps)
            avg_pace_s = float(clean_laps["LapTime"].median())

            # Calculate degradation slope (seconds gained per lap)
            tyre_life = clean_laps["TyreLife"].values if "TyreLife" in clean_laps.columns else np.arange(stint_length)
            lap_times = clean_laps["LapTime"].values
            
            deg_slope = 0.0
            if len(tyre_life) >= 3 and np.std(tyre_life) > 0:
                res = linregress(tyre_life, lap_times)
                deg_slope = float(res.slope)

            stints.append({
                "driver_id": str(driver),
                "stint_number": int(stint_num),
                "compound": str(compound),
                "start_lap": start_lap,
                "end_lap": end_lap,
                "stint_length": stint_length,
                "avg_pace_s": avg_pace_s,
                "pace_degradation_s_per_lap": deg_slope,
                "cliff_detected": deg_slope > 0.15,
            })

        return pd.DataFrame(stints)
