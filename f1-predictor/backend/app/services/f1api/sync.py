"""Sync f1api.dev data into the application database (read model).

Provenance: every dataset upsert writes a DatasetProvenance row with
source / season / event / retrieved_at / data_version (Phase 5).

Internal ids stay stable: race id = "{year}_{round}" (existing convention),
driver ids match Ergast-style ids so the prediction engine keeps working.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ChampionshipStanding,
    Circuit,
    DatasetProvenance,
    Driver,
    DriverTeamSeason,
    QualifyingResult,
    Race,
    RaceResult,
    Season,
    Team,
)
from app.services.f1api.client import F1ApiClient, F1ApiError
from app.services.f1api.normalize import parse_float, parse_int, parse_lap_time

logger = logging.getLogger("f1api_sync")

SOURCE = "f1api.dev"
DATA_VERSION = "1.0"


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


class F1ApiSync:
    def __init__(self, db: AsyncSession, client: Optional[F1ApiClient] = None):
        self.db = db
        self.client = client or F1ApiClient()

    # ------------------------------------------------------------------ #
    async def _provenance(
        self,
        dataset: str,
        season: Optional[int],
        status: str = "ok",
        detail: Optional[str] = None,
        event: Optional[str] = None,
    ) -> None:
        row = await self.db.get(DatasetProvenance, dataset)
        if row is None:
            row = DatasetProvenance(dataset=dataset, source=SOURCE, season=season)
            self.db.add(row)
        row.retrieved_at = datetime.now(timezone.utc)
        row.data_version = DATA_VERSION
        row.status = status
        row.detail = detail
        row.source = SOURCE
        row.season = season
        row.event = event

    # ------------------------------------------------------------------ #
    # Calendar: seasons + circuits + races
    # ------------------------------------------------------------------ #
    async def sync_calendar(self, year: int) -> Dict[str, int]:
        try:
            data = await self.client.season_calendar(year)
        except F1ApiError as exc:
            await self._provenance(f"calendar:{year}", year, status="error", detail=str(exc))
            await self.db.commit()
            raise

        season_year = int(data.get("season") or year)
        races_raw = data.get("races") or []
        if not isinstance(races_raw, list):
            raise F1ApiError(f"Unexpected calendar payload for {year}")

        if await self.db.get(Season, season_year) is None:
            self.db.add(Season(year=season_year, regulation_era="ground_effect"))

        count = 0
        today = date.today()
        for r in races_raw:
            rnd = parse_int(r.get("round"))
            if rnd is None:
                continue
            race_id = f"{season_year}_{rnd}"
            schedule = r.get("schedule") or {}
            race_sched = schedule.get("race") or {}
            circ = r.get("circuit") or {}
            if isinstance(circ, list):
                circ = circ[0] if circ else {}

            circuit_id = circ.get("circuitId")
            if circuit_id:
                await self._upsert_circuit(circ)

            race_date = _parse_date(race_sched.get("date"))
            is_sprint = bool(
                (schedule.get("sprintRace") or {}).get("date")
                or (schedule.get("sprintQualy") or {}).get("date")
            )
            race = await self.db.get(Race, race_id)
            if race is None:
                race = Race(id=race_id, season_year=season_year, round_number=rnd,
                            circuit_id=circuit_id or "unknown", name=r.get("raceName") or race_id)
                self.db.add(race)
            race.official_name = r.get("raceName") or race.official_name
            race.race_date = race_date or race.race_date
            race.race_time = race_sched.get("time") or race.race_time
            race.total_laps = parse_int(r.get("laps")) or race.total_laps
            race.is_sprint_weekend = is_sprint
            race.circuit_id = circuit_id or race.circuit_id
            if race.status != "completed" and race_date is not None:
                race.status = "completed" if race_date < today else "scheduled"
            count += 1

        await self._provenance(f"calendar:{year}", season_year)
        await self.db.commit()
        logger.info("Calendar synced", extra={"season": season_year, "races": count})
        return {"season": season_year, "races": count}

    async def _upsert_circuit(self, circ: Dict[str, Any]) -> None:
        cid = circ.get("circuitId")
        if not cid:
            return
        length_raw = circ.get("circuitLength")  # e.g. "4940km"
        length_km = None
        if length_raw:
            length_km = parse_float(str(length_raw).lower().replace("km", ""))
            if length_km and length_km > 500:  # stored in metres in source
                length_km = length_km / 1000.0
        c = await self.db.get(Circuit, cid)
        if c is None:
            c = Circuit(id=cid, name=circ.get("circuitName") or cid)
            self.db.add(c)
        c.name = circ.get("circuitName") or c.name
        c.country = circ.get("country") or c.country
        c.locality = circ.get("city") or c.locality
        c.length_km = length_km if length_km is not None else c.length_km
        c.num_corners = parse_int(circ.get("corners")) or c.num_corners
        lap_rec = parse_lap_time(circ.get("lapRecord"))
        if lap_rec is not None:
            c.lap_record_seconds = lap_rec

    # ------------------------------------------------------------------ #
    # Grid: drivers + teams + SEASON-SCOPED assignment (Phase 3)
    # ------------------------------------------------------------------ #
    async def sync_grid(self, year: int) -> Dict[str, int]:
        try:
            drivers_raw = await self.client.season_drivers(year)
            teams_raw = await self.client.season_teams(year)
        except F1ApiError as exc:
            await self._provenance(f"grid:{year}", year, status="error", detail=str(exc))
            await self.db.commit()
            raise

        for t in teams_raw:
            tid = t.get("teamId")
            if not tid:
                continue
            team = await self.db.get(Team, tid)
            if team is None:
                team = Team(id=tid, name=t.get("teamName") or tid)
                self.db.add(team)
            team.name = t.get("teamName") or team.name
            team.nationality = t.get("teamNationality") or team.nationality

        for d in drivers_raw:
            did = d.get("driverId")
            if not did:
                continue
            driver = await self.db.get(Driver, did)
            if driver is None:
                driver = Driver(id=did, first_name=d.get("name") or "", last_name=d.get("surname") or did)
                self.db.add(driver)
            driver.code = d.get("shortName") or driver.code
            driver.number = parse_int(d.get("number")) if d.get("number") is not None else driver.number
            driver.first_name = d.get("name") or driver.first_name
            driver.last_name = d.get("surname") or driver.last_name
            driver.nationality = d.get("nationality") or driver.nationality
            driver.dob = _parse_date(d.get("birthday")) or driver.dob
            await self.db.flush()

            team_id = d.get("teamId")
            if team_id:
                stmt = select(DriverTeamSeason).where(
                    DriverTeamSeason.driver_id == did,
                    DriverTeamSeason.season_year == year,
                )
                assignment = (await self.db.execute(stmt)).scalar_one_or_none()
                if assignment is None:
                    self.db.add(DriverTeamSeason(driver_id=did, team_id=team_id, season_year=year))
                elif assignment.team_id != team_id:
                    assignment.team_id = team_id  # mid-season change, history stays in race_results

        await self._provenance(f"grid:{year}", year)
        await self.db.commit()
        return {"drivers": len(drivers_raw), "teams": len(teams_raw)}

    # ------------------------------------------------------------------ #
    # Official standings (Phase 5 provenance, source f1api.dev)
    # ------------------------------------------------------------------ #
    async def sync_standings(self, year: int) -> Dict[str, int]:
        try:
            drivers_raw = await self.client.drivers_championship(year)
            teams_raw = await self.client.constructors_championship(year)
        except F1ApiError as exc:
            await self._provenance(f"standings:{year}", year, status="error", detail=str(exc))
            await self.db.commit()
            raise

        n_d = 0
        for row in drivers_raw:
            did = row.get("driverId")
            pos = parse_int(row.get("position"))
            if did is None or pos is None:
                continue
            await self._upsert_standing(year, "driver", did, pos, float(row.get("points") or 0), int(row.get("wins") or 0))
            n_d += 1
        n_t = 0
        for row in teams_raw:
            tid = row.get("teamId")
            pos = parse_int(row.get("position"))
            if tid is None or pos is None:
                continue
            await self._upsert_standing(year, "constructor", tid, pos, float(row.get("points") or 0), int(row.get("wins") or 0))
            n_t += 1

        await self._provenance(f"standings:{year}", year)
        await self.db.commit()
        return {"drivers": n_d, "constructors": n_t}

    async def _upsert_standing(self, year: int, entity_type: str, entity_id: str, position: int, points: float, wins: int) -> None:
        stmt = select(ChampionshipStanding).where(
            ChampionshipStanding.season == year,
            ChampionshipStanding.entity_type == entity_type,
            ChampionshipStanding.entity_id == entity_id,
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = ChampionshipStanding(
                season=year, entity_type=entity_type, entity_id=entity_id,
                position=position, points=points, wins=wins, source=SOURCE,
            )
            self.db.add(row)
        else:
            row.position = position
            row.points = points
            row.wins = wins
            row.source = SOURCE

    # ------------------------------------------------------------------ #
    # Event results / qualifying (historical, source f1api.dev)
    # ------------------------------------------------------------------ #
    async def sync_event(self, year: int, round_: int) -> Dict[str, int]:
        race_id = f"{year}_{round_}"
        race = await self.db.get(Race, race_id)
        if race is None:
            raise F1ApiError(f"Race {race_id} not in calendar — sync calendar first")

        n_results = 0
        n_quali = 0
        try:
            race_data = (await self.client.race_results(year, round_)).get("races") or {}
            results = race_data.get("results") or []
        except F1ApiError:
            results = []

        for r in results:
            drv = r.get("driver") or {}
            tm = r.get("team") or {}
            driver_id = drv.get("driverId")
            team_id = tm.get("teamId")
            if not driver_id or not team_id:
                continue
            await self._ensure_driver_team(driver_id, drv, team_id, tm, year)

            stmt = select(RaceResult).where(RaceResult.race_id == race_id, RaceResult.driver_id == driver_id)
            row = (await self.db.execute(stmt)).scalar_one_or_none()
            pos = parse_int(r.get("position"))
            retired = r.get("retired")
            is_dnf = bool(retired) or pos is None
            if row is None:
                row = RaceResult(race_id=race_id, driver_id=driver_id, team_id=team_id, source=SOURCE)
                self.db.add(row)
            row.team_id = team_id  # event-scoped team (historical accuracy)
            row.grid_position = parse_int(r.get("grid"))
            row.finish_position = pos
            row.classified = not is_dnf
            row.dnf = is_dnf
            row.status_detail = str(retired) if retired else None
            row.points = float(r.get("points") or 0)
            row.fastest_lap_time_s = parse_lap_time(r.get("fastLap"))
            row.race_time_s = parse_lap_time(r.get("time"))
            n_results += 1

        try:
            qualy_data = (await self.client.qualifying(year, round_)).get("races") or {}
            qualy_rows = qualy_data.get("qualyResults") or []
        except F1ApiError:
            qualy_rows = []

        for i, q in enumerate(qualy_rows):
            driver_id = q.get("driverId")
            team_id = q.get("teamId")
            if not driver_id or not team_id:
                continue
            await self._ensure_driver_team(driver_id, q.get("driver") or {}, team_id, q.get("team") or {}, year)
            stmt = select(QualifyingResult).where(
                QualifyingResult.race_id == race_id, QualifyingResult.driver_id == driver_id
            )
            row = (await self.db.execute(stmt)).scalar_one_or_none()
            q1 = parse_lap_time(q.get("q1"))
            q2 = parse_lap_time(q.get("q2"))
            q3 = parse_lap_time(q.get("q3"))
            best = min([t for t in (q3, q2, q1) if t is not None], default=None)
            if row is None:
                row = QualifyingResult(race_id=race_id, driver_id=driver_id, team_id=team_id, source=SOURCE)
                self.db.add(row)
            row.team_id = team_id
            row.position = i + 1  # array order is classification order
            row.q1_time_s, row.q2_time_s, row.q3_time_s = q1, q2, q3
            row.best_time_s = best
            n_quali += 1

        if n_results > 0:
            race.status = "completed"

        await self._provenance(f"event:{race_id}", year, event=race_id)
        await self.db.commit()
        return {"results": n_results, "qualifying": n_quali}

    async def _ensure_driver_team(
        self, driver_id: str, drv: Dict[str, Any], team_id: str, tm: Dict[str, Any], year: int
    ) -> None:
        driver = await self.db.get(Driver, driver_id)
        if driver is None:
            driver = Driver(
                id=driver_id,
                first_name=drv.get("name") or "",
                last_name=drv.get("surname") or driver_id,
            )
            self.db.add(driver)
        driver.code = drv.get("shortName") or driver.code
        driver.number = parse_int(drv.get("number")) if drv.get("number") is not None else driver.number
        driver.nationality = drv.get("nationality") or driver.nationality
        await self.db.flush()

        team = await self.db.get(Team, team_id)
        if team is None:
            self.db.add(Team(id=team_id, name=tm.get("teamName") or team_id, nationality=tm.get("nationality")))
            await self.db.flush()

        stmt = select(DriverTeamSeason).where(
            DriverTeamSeason.driver_id == driver_id, DriverTeamSeason.season_year == year
        )
        if not (await self.db.execute(stmt)).scalar_one_or_none():
            self.db.add(DriverTeamSeason(driver_id=driver_id, team_id=team_id, season_year=year))

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    async def sync_season(self, year: int, include_events: bool = True) -> Dict[str, Any]:
        summary: Dict[str, Any] = {"season": year}
        summary["calendar"] = await self.sync_calendar(year)
        summary["grid"] = await self.sync_grid(year)
        summary["standings"] = await self.sync_standings(year)

        if include_events:
            races = (
                (await self.db.execute(select(Race).where(Race.season_year == year).order_by(Race.round_number)))
                .scalars()
                .all()
            )
            today = date.today()
            results_total = 0
            quali_total = 0
            for race in races:
                if race.race_date is None or race.race_date <= today:
                    try:
                        res = await self.sync_event(year, race.round_number)
                        results_total += res["results"]
                        quali_total += res["qualifying"]
                    except F1ApiError as exc:
                        logger.warning("Event sync failed: %s", exc)
                    await asyncio.sleep(0.15)
            summary["results"] = results_total
            summary["qualifying"] = quali_total
        return summary

    async def close(self) -> None:
        await self.client.close()

