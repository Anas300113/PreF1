from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.jolpica_client import JolpicaClient
from app.models import Circuit, Season, Race, Driver, Team, DriverTeamSeason, RaceEntry, QualifyingResult, RaceResult, PitStop
from app.utils.circuit_profiles import get_circuit_profile
from app.utils.time_utils import to_seconds, parse_jolpica_date, regulation_era
from app.utils.logging_config import get_logger

logger = get_logger("jolpica_ingestor")

def utcnow():
    return datetime.now(timezone.utc)

class JolpicaIngestor:
    def __init__(self, db_session: AsyncSession, client: JolpicaClient):
        self.db = db_session
        self.client = client

    async def ingest_circuits(self) -> int:
        raw_circuits = await self.client.get_circuits()
        count = 0
        for c in raw_circuits:
            circuit_id = c["circuitId"]
            loc = c.get("Location", {})
            profile = get_circuit_profile(circuit_id)

            lat = float(loc.get("lat")) if loc.get("lat") else None
            lon = float(loc.get("long")) if loc.get("long") else None

            existing = await self.db.get(Circuit, circuit_id)
            if existing:
                existing.name = c.get("circuitName", existing.name)
                existing.country = loc.get("country", existing.country)
                existing.locality = loc.get("locality", existing.locality)
                existing.latitude = lat or existing.latitude
                existing.longitude = lon or existing.longitude
            else:
                circuit = Circuit(
                    id=circuit_id,
                    name=c.get("circuitName", circuit_id),
                    country=loc.get("country"),
                    locality=loc.get("locality"),
                    latitude=lat,
                    longitude=lon,
                    num_corners=profile.get("num_corners"),
                    overtaking_difficulty=profile.get("overtaking_difficulty"),
                    pit_loss_seconds=profile.get("pit_loss_seconds"),
                    tyre_degradation_index=profile.get("tyre_degradation_index"),
                    safety_car_rate=profile.get("safety_car_rate"),
                    circuit_type=profile.get("circuit_type"),
                )
                self.db.add(circuit)
            count += 1
        await self.db.commit()
        logger.info("Ingested circuits", count=count)
        return count

    async def ingest_seasons(self, start_year: int = 2010, end_year: Optional[int] = None) -> int:
        current_year = datetime.now().year
        end_year = end_year or current_year
        count = 0
        for yr in range(start_year, end_year + 1):
            existing = await self.db.get(Season, yr)
            if not existing:
                season = Season(
                    year=yr,
                    regulation_era=regulation_era(yr)
                )
                self.db.add(season)
                count += 1
        await self.db.commit()
        return count

    async def ingest_races(self, year: int) -> int:
        raw_races = await self.client.get_races(year)
        count = 0
        for r in raw_races:
            race_id = f"{year}_{r['round']}"
            circuit_id = r.get("Circuit", {}).get("circuitId")
            
            # Ensure circuit exists
            if circuit_id:
                c_exists = await self.db.get(Circuit, circuit_id)
                if not c_exists:
                    c_loc = r.get("Circuit", {}).get("Location", {})
                    profile = get_circuit_profile(circuit_id)
                    new_c = Circuit(
                        id=circuit_id,
                        name=r.get("Circuit", {}).get("circuitName", circuit_id),
                        country=c_loc.get("country"),
                        locality=c_loc.get("locality"),
                        latitude=float(c_loc.get("lat")) if c_loc.get("lat") else None,
                        longitude=float(c_loc.get("long")) if c_loc.get("long") else None,
                        **profile
                    )
                    self.db.add(new_c)

            race_date = parse_jolpica_date(r.get("date"))
            is_sprint = "Sprint" in r or "sprint" in r

            existing = await self.db.get(Race, race_id)
            if existing:
                existing.name = r.get("raceName", existing.name)
                existing.race_date = race_date or existing.race_date
                existing.race_time = r.get("time", existing.race_time)
                existing.is_sprint_weekend = is_sprint
            else:
                race = Race(
                    id=race_id,
                    season_year=year,
                    round_number=int(r["round"]),
                    circuit_id=circuit_id,
                    name=r.get("raceName", f"Grand Prix {r['round']}"),
                    official_name=r.get("raceName"),
                    race_date=race_date,
                    race_time=r.get("time"),
                    is_sprint_weekend=is_sprint,
                    status="completed" if race_date and race_date < datetime.now().date() else "scheduled"
                )
                self.db.add(race)
            count += 1
        await self.db.commit()
        return count

    async def ingest_race_results(self, year: int, round_num: int) -> int:
        race_id = f"{year}_{round_num}"
        raw_results = await self.client.get_results(year, round_num)
        count = 0

        for r in raw_results:
            d_info = r.get("Driver", {})
            c_info = r.get("Constructor", {})
            driver_id = d_info["driverId"]
            team_id = c_info["constructorId"]

            # Ensure Driver and Team exist
            await self._ensure_driver(d_info)
            await self._ensure_team(c_info)

            # DriverTeamSeason mapping
            dts_stmt = select(DriverTeamSeason).where(
                DriverTeamSeason.driver_id == driver_id, DriverTeamSeason.season_year == year
            )
            res = await self.db.execute(dts_stmt)
            if not res.scalar_one_or_none():
                self.db.add(DriverTeamSeason(driver_id=driver_id, team_id=team_id, season_year=year))

            # RaceEntry mapping
            re_stmt = select(RaceEntry).where(
                RaceEntry.race_id == race_id, RaceEntry.driver_id == driver_id
            )
            res_re = await self.db.execute(re_stmt)
            if not res_re.scalar_one_or_none():
                self.db.add(RaceEntry(race_id=race_id, driver_id=driver_id, team_id=team_id))

            status_str = r.get("status", "")
            is_dnf = self._map_status_to_dnf(status_str)
            race_time_s = to_seconds(r.get("Time", {}).get("time")) if "Time" in r else None

            # Upsert RaceResult
            stmt = select(RaceResult).where(RaceResult.race_id == race_id, RaceResult.driver_id == driver_id)
            existing = (await self.db.execute(stmt)).scalar_one_or_none()

            grid_pos = int(r.get("grid", 0)) if r.get("grid") else None
            finish_pos = int(r.get("position", 0)) if r.get("position") and r.get("position").isdigit() else None
            pts = float(r.get("points", 0.0))

            if existing:
                existing.grid_position = grid_pos
                existing.finish_position = finish_pos
                existing.status_detail = status_str
                existing.dnf = is_dnf
                existing.points = pts
                existing.race_time_s = race_time_s
            else:
                rr = RaceResult(
                    race_id=race_id,
                    driver_id=driver_id,
                    team_id=team_id,
                    grid_position=grid_pos,
                    finish_position=finish_pos,
                    classified=(r.get("positionText") != "R" and not is_dnf),
                    status_code=r.get("statusId"),
                    status_detail=status_str,
                    dnf=is_dnf,
                    laps_completed=int(r.get("laps", 0)) if r.get("laps") else None,
                    race_time_s=race_time_s,
                    points=pts,
                    fastest_lap=(r.get("FastestLap", {}).get("rank") == "1"),
                    fastest_lap_time_s=to_seconds(r.get("FastestLap", {}).get("Time", {}).get("time")),
                    source="jolpica"
                )
                self.db.add(rr)
            count += 1

        await self.db.commit()
        return count

    async def ingest_pit_stops(self, year: int, round_num: int) -> int:
        """Ingest pit stops for a race (run AFTER results so drivers exist)."""
        race_id = f"{year}_{round_num}"
        raw_stops = await self.client.get_pit_stops(year, round_num)
        count = 0

        for s in raw_stops:
            driver_id = s.get("driverId")
            if not driver_id:
                continue

            # Skip stops for drivers missing from the drivers table (FK guard)
            exists = (
                await self.db.execute(select(Driver.id).where(Driver.id == driver_id).limit(1))
            ).scalar_one_or_none()
            if not exists:
                continue

            stop_number = int(s["stop"]) if str(s.get("stop", "")).isdigit() else None
            lap = int(s["lap"]) if str(s.get("lap", "")).isdigit() else None
            duration_s = to_seconds(s.get("duration"))

            if stop_number is None or lap is None:
                continue

            stmt = select(PitStop).where(
                PitStop.race_id == race_id,
                PitStop.driver_id == driver_id,
                PitStop.stop_number == stop_number,
            )
            existing = (await self.db.execute(stmt)).scalar_one_or_none()

            if existing:
                existing.lap = lap
                existing.duration_s = duration_s
            else:
                self.db.add(
                    PitStop(
                        race_id=race_id,
                        driver_id=driver_id,
                        stop_number=stop_number,
                        lap=lap,
                        duration_s=duration_s,
                        source="jolpica",
                    )
                )
            count += 1

        await self.db.commit()
        return count

    async def ingest_qualifying_results(self, year: int, round_num: int) -> int:
        race_id = f"{year}_{round_num}"
        raw_quali = await self.client.get_qualifying(year, round_num)
        if not raw_quali:
            return 0

        pole_time_s = None
        for q in raw_quali:
            if q.get("position") == "1":
                q3 = to_seconds(q.get("Q3"))
                q2 = to_seconds(q.get("Q2"))
                q1 = to_seconds(q.get("Q1"))
                pole_time_s = q3 or q2 or q1
                break

        count = 0
        for q in raw_quali:
            d_info = q.get("Driver", {})
            c_info = q.get("Constructor", {})
            driver_id = d_info["driverId"]
            team_id = c_info["constructorId"]

            await self._ensure_driver(d_info)
            await self._ensure_team(c_info)

            q1_s = to_seconds(q.get("Q1"))
            q2_s = to_seconds(q.get("Q2"))
            q3_s = to_seconds(q.get("Q3"))
            valid_times = [t for t in [q3_s, q2_s, q1_s] if t is not None]
            best_s = min(valid_times) if valid_times else None

            gap_to_pole = (best_s - pole_time_s) if (best_s and pole_time_s) else None
            rel_pace = (best_s / pole_time_s) if (best_s and pole_time_s) else None

            stmt = select(QualifyingResult).where(QualifyingResult.race_id == race_id, QualifyingResult.driver_id == driver_id)
            existing = (await self.db.execute(stmt)).scalar_one_or_none()

            pos = int(q.get("position")) if q.get("position") and q.get("position").isdigit() else None

            if existing:
                existing.position = pos
                existing.best_time_s = best_s
                existing.gap_to_pole_s = gap_to_pole
                existing.relative_pace = rel_pace
            else:
                qr = QualifyingResult(
                    race_id=race_id,
                    driver_id=driver_id,
                    team_id=team_id,
                    position=pos,
                    q1_time_s=q1_s,
                    q2_time_s=q2_s,
                    q3_time_s=q3_s,
                    best_time_s=best_s,
                    gap_to_pole_s=gap_to_pole,
                    relative_pace=rel_pace,
                    source="jolpica"
                )
                self.db.add(qr)
            count += 1

        await self.db.commit()
        return count

    async def ingest_full_season(self, year: int) -> dict:
        logger.info("Starting full season ingestion", year=year)
        await self.ingest_seasons(year, year)
        n_races = await self.ingest_races(year)
        
        n_results = 0
        n_quali = 0
        n_pits = 0
        for r in range(1, n_races + 1):
            n_results += await self.ingest_race_results(year, r)
            n_quali += await self.ingest_qualifying_results(year, r)
            n_pits += await self.ingest_pit_stops(year, r)
            
        summary = {
            "year": year,
            "races": n_races,
            "results": n_results,
            "qualifying": n_quali,
            "pit_stops": n_pits,
        }
        logger.info("Completed season ingestion", **summary)
        return summary

    async def _ensure_driver(self, d_info: dict):
        d_id = d_info["driverId"]
        existing = await self.db.get(Driver, d_id)
        if not existing:
            driver = Driver(
                id=d_id,
                code=d_info.get("code"),
                number=int(d_info["permanentNumber"]) if d_info.get("permanentNumber") else None,
                first_name=d_info.get("givenName", ""),
                last_name=d_info.get("familyName", ""),
                nationality=d_info.get("nationality"),
                dob=parse_jolpica_date(d_info.get("dateOfBirth")),
            )
            self.db.add(driver)
            # Flush so subsequent db.get() calls and UNIQUE constraints see it
            await self.db.flush()

    async def _ensure_team(self, c_info: dict):
        c_id = c_info["constructorId"]
        existing = await self.db.get(Team, c_id)
        if not existing:
            team = Team(
                id=c_id,
                name=c_info.get("name", c_id),
                nationality=c_info.get("nationality"),
            )
            self.db.add(team)
            # Flush so subsequent db.get() calls and UNIQUE constraints see it
            await self.db.flush()

    def _map_status_to_dnf(self, status: str) -> bool:
        if not status:
            return False
        clean = status.lower()
        if "finished" in clean or "lap" in clean or "laps" in clean:
            return False
        return True
