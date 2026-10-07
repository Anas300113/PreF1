import sys
from pathlib import Path
import pytest
from sqlalchemy import select
from app.database import Base  # noqa: E402
from app.models import (  # noqa: E402
    ChampionshipStanding,
    DatasetProvenance,
    Driver,
    DriverTeamSeason,
    QualifyingResult,
    Race,
    RaceResult,
    Season,
    Team,
)
from app.services.f1api.sync import F1ApiSync  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
class FakeClient:
    """Canned f1api.dev responses (mirrors the live API shapes)."""
    def __init__(self, state):
        self.state = state
    async def season_calendar(self, year=None):
        return self.state["calendar"]
    async def season_drivers(self, year):
        return self.state["drivers"]
    async def season_teams(self, year):
        return self.state["teams"]
    async def drivers_championship(self, year):
        return self.state["driver_standings"]
    async def constructors_championship(self, year):
        return self.state["constructor_standings"]
    async def race_results(self, year, round_):
        if round_ != 1:
            return {"races": {}}
        return self.state["race"]
    async def qualifying(self, year, round_):
        if round_ != 1:
            return {"races": {}}
        return self.state["qualy"]
def _db_engine(tmp_path):
    from sqlalchemy.ext.asyncio import create_async_engine

    return create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db", future=True)

def _session_factory(engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False,
                              autocommit=False, autoflush=False)

async def _init_db(engine):
    from app.database import Base as _Base

    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
def _drivers(count: int):
    names = [
        ("Max", "Verstappen"), ("Charles", "Leclerc"), ("Lewis", "Hamilton"),
        ("George", "Russell"), ("Lando", "Norris"), ("Oscar", "Piastri"),
        ("Fernando", "Alonso"), ("Sergio", "Perez"), ("Carlos", "Sainz"),
    ]
    out = []
    for i in range(count):
        first, last = names[i % len(names)]
        out.append(
            {
                "driverId": f"d{i:02d}",
                "name": first,
                "surname": last,
                "nationality": "Netherlands" if i == 0 else "Monaco",
                "birthday": "1997-09-30" if i == 0 else "1997-01-01",
                "number": 1 if i == 0 else (i + 1) % 20,
                "shortName": "VER" if i == 0 else f"D{i:02d}",
                "teamId": f"t{(i // 4) % 6}",
            }
        )
    return out
def _teams():
    return [
        {"teamId": "red_bull", "teamName": "Red Bull Racing", "teamNationality": "Austria"},
        {"teamId": "mercedes", "teamName": "Mercedes AMG F1 Team", "teamNationality": "Germany"},
        {"teamId": "ferrari", "teamName": "Scuderia Ferrari", "teamNationality": "Italy"},
        {"teamId": "mclaren", "teamName": "McLaren F1 Team", "teamNationality": "UK"},
        {"teamId": "alpine", "teamName": "Alpine F1 Team", "teamNationality": "Monaco"},
        {"teamId": "rb", "teamName": "RB F1 Team", "teamNationality": "Singapore"},
    ]
def _calendar():
    races = []
    now = __import__("datetime").date.today()
    for rnd in (1, 2, 3, 4):
        date = f"2026-03-{rnd:02d}"
        is_sprint = rnd == 2
        status = "completed" if date < str(now) else "scheduled"
        race = {
            "round": rnd,
            "raceName": f"Test Grand Prix {rnd}",
            "schedule": {"race": {"date": date, "time": "14:00"}},
            "laps": 57,
            "circuit": {
                "circuitId": f"circuit_{rnd}",
                "circuitName": f"Circuit {rnd}",
                "country": "Test",
                "city": "Village",
                "circuitLength": "6051km",
                "corners": 15,
                "lapRecord": "1:35.867",
                "winner": {"driverId": "max_verstappen", "teamId": "red_bull"},
            },
            "winner": {"driverId": "max_verstappen", "teamId": "red_bull"},
        }
        if is_sprint:
            race["schedule"]["sprintRace"] = {"date": "2026-03-14", "time": "12:00"}
        races.append(race)
    return {"season": 2026, "races": races}
def _race_payload(drivers, round_):
    results = []
    for d in drivers:
        results.append(
            {
                "position": 1,
                "points": 25.0,
                "grid": 1,
                "time": "1:30:12.345",
                "fastLap": "1:31.234",
                "retired": None,
                "driver": {"driverId": d["driverId"], "name": d["name"], "surname": d["surname"]},
                "team": {"teamId": d["teamId"], "teamName": "Test Team"},
            }
        )
    return {
        "races": {
            "round": round_, "date": "2026-03-" + str(round_), "raceName": "Test GP " + str(round_),
            "results": results,
            "circuit": {
                "circuitId": "circuit_" + str(round_), "circuitName": "Circuit " + str(round_),
                "country": "Test", "city": "Village",
            },
        }
    }
def _qualy_payload(drivers, round_):
    rows = []
    for i, d in enumerate(drivers):
        rows.append(
            {
                "driverId": d["driverId"],
                "teamId": d["teamId"],
                "q1": "1:35.867",
                "q2": "1:36.100",
                "q3": "1:35.500",
                "gridPosition": i + 1,
                "driver": {"driverId": d["driverId"], "name": d["name"], "surname": d["surname"]},
                "team": {"teamId": d["teamId"], "teamName": "Test Team"},
            }
        )
    return {
        "races": {
            "round": round_, "date": "2026-03-" + str(round_),
            "circuit": {
                "circuitId": "circuit_" + str(round_), "circuitName": "Circuit " + str(round_),
                "country": "Test", "city": "Village",
            },
            "qualyResults": rows,
        }
    }
class TestSyncGrid:
    @pytest.mark.asyncio
    async def test_drivers_teams_and_season_assignment(self, tmp_path):
        from sqlalchemy import select
        drv = _drivers(10)
        state = {
            "drivers": drv,
            "teams": _teams(),
        }
        engine = _db_engine(tmp_path)
        session_factory = _session_factory(engine)
        await _init_db(engine)
        try:
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                await sync.sync_grid(2026)
                await session.commit()
                drivers = (await session.execute(select(Driver).order_by(Driver.id))).scalars().all()
                teams = (await session.execute(select(Team).order_by(Team.id))).scalars().all()
                assignments = (await session.execute(select(DriverTeamSeason))).scalars().all()
            assert [d.id for d in drivers] == [f"d{i:02d}" for i in range(10)]
            assert {d.id: d.code for d in drivers} == {
                "d00": "VER", "d01": "D01", "d02": "D02", "d03": "D03", "d04": "D04",
                "d05": "D05", "d06": "D06", "d07": "D07", "d08": "D08", "d09": "D09",
            }
            assert {t.id: t.name for t in teams} == {
                "red_bull": "Red Bull Racing", "mercedes": "Mercedes AMG F1 Team",
                "ferrari": "Scuderia Ferrari", "mclaren": "McLaren F1 Team",
                "alpine": "Alpine F1 Team", "rb": "RB F1 Team",
            }
            assert len(assignments) == 10
            assert {a.driver_id: a.team_id for a in assignments} == {
                "d00": "t0", "d01": "t0", "d02": "t0", "d03": "t0", "d04": "t1",
                "d05": "t1", "d06": "t1", "d07": "t1", "d08": "t2", "d09": "t2",
            }
        finally:
            await engine.dispose()
    @pytest.mark.asyncio
    async def test_mid_season_team_change_keeps_historical_grid(self, tmp_path):
        from sqlalchemy import select
        drv = _drivers(1)
        state = {"drivers": drv, "teams": _teams(), "calendar": _calendar(), "qualy": _qualy_payload(drv, 1)}
        engine = _db_engine(tmp_path)
        session_factory = _session_factory(engine)
        await _init_db(engine)
        try:
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                state["race"] = _race_payload(drv, 1)
                state["race"]["races"]["results"][0]["team"] = {"teamId": "t9", "teamName": "Other"}
                await sync.sync_grid(2026)
                await sync.sync_calendar(2026)
                await sync.sync_event(2026, 1)
                await session.commit()
                row = (
                    await session.execute(
                        select(DriverTeamSeason).where(DriverTeamSeason.driver_id == "d00")
                    )
                ).scalar_one()
                r = (
                    await session.execute(select(RaceResult).where(RaceResult.driver_id == "d00"))
                ).scalar_one()
            assert row.team_id == "t0"  # grid year assignment unchanged
            assert r.team_id == "t9"  # event-scoped result is event-scoped
        finally:
            await engine.dispose()
class TestSyncStandings:
    @pytest.mark.asyncio
    async def test_standings_upsert_and_derive_positions(self, tmp_path):
        from sqlalchemy import select
        state = {
            "drivers": _drivers(6),
            "teams": _teams(),
            "driver_standings": [
                {"position": "1", "points": 320.0, "wins": 1, "driverId": "d00", "teamId": "t0"},
                {"position": "2", "points": 236.0, "wins": 0, "driverId": "d01", "teamId": "t0"},
            ],
            "constructor_standings": [
                {"position": "1", "points": 310.0, "wins": 0, "teamId": "red_bull"},
            ],
        }
        engine = _db_engine(tmp_path)
        session_factory = _session_factory(engine)
        await _init_db(engine)
        try:
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                await sync.sync_standings(2026)
                await session.commit()
                drvs = (
                    await session.execute(
                        select(ChampionshipStanding).where(ChampionshipStanding.entity_type == "driver")
                    )
                ).scalars().all()
                cons = (
                    await session.execute(
                        select(ChampionshipStanding).where(ChampionshipStanding.entity_type == "constructor")
                    )
                ).scalars().all()
            assert [(s.entity_id, s.position, s.points) for s in drvs] == [
                ("d00", 1, 320.0), ("d01", 2, 236.0),
            ]
            assert [(c.entity_id, c.position, c.points) for c in cons] == [("red_bull", 1, 310.0)]
            assert all(s.source == "f1api.dev" for s in drvs + cons)
            state["driver_standings"][0]["points"] = 330.0
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                await sync.sync_standings(2026)
                await session.commit()
                first = (
                    await session.execute(
                        select(ChampionshipStanding).where(ChampionshipStanding.entity_id == "d00")
                    )
                ).scalar_one()
            assert first.points == 330.0
        finally:
            await engine.dispose()
class TestSyncEvent:
    @pytest.mark.asyncio
    async def test_event_writes_results_qualifying_and_provenance(self, tmp_path):
        drv = _drivers(4)
        state = {
            "drivers": drv,
            "teams": _teams(),
            "calendar": _calendar(),
            "race": _race_payload(drv, 1),
            "qualy": _qualy_payload(drv, 1),
        }
        engine = _db_engine(tmp_path)
        session_factory = _session_factory(engine)
        await _init_db(engine)
        try:
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                await sync.sync_calendar(2026)
                await sync.sync_event(2026, 1)
                await session.commit()
                results = (
                    await session.execute(select(RaceResult).order_by(RaceResult.driver_id))
                ).scalars().all()
                quali = (
                    await session.execute(select(QualifyingResult).order_by(QualifyingResult.driver_id))
                ).scalars().all()
                race = (
                    await session.execute(select(Race).where(Race.id == "2026_1"))
                ).scalar_one()
                provenance = (
                    await session.execute(
                        select(DatasetProvenance).where(DatasetProvenance.dataset == "event:2026_1")
                    )
                ).scalar_one()
            assert len(results) == 4
            assert {r.driver_id: r.finish_position for r in results} == {
                "d00": 1, "d01": 1, "d02": 1, "d03": 1,
            }
            assert {r.team_id for r in results} == {"t0"}
            assert all(r.source == "f1api.dev" for r in results)
            assert {r.race_id for r in results} == {"2026_1"}
            assert len(quali) == 4
            assert {q.driver_id: q.position for q in quali} == {"d00": 1, "d01": 2, "d02": 3, "d03": 4}
            assert all(
                q.q1_time_s == pytest.approx(95.867) and q.q2_time_s == pytest.approx(96.1)
                and q.q3_time_s == pytest.approx(95.5) for q in quali
            )
            assert race.status == "completed"
            assert race.total_laps == 57
            assert race.race_time == "14:00"
            assert provenance.season == 2026 and provenance.event == "2026_1"
        finally:
            await engine.dispose()
class TestSyncSeason:
    @pytest.mark.asyncio
    async def test_sync_season_processes_available_events(self, tmp_path):
        drv = _drivers(6)
        state = {
            "drivers": drv,
            "teams": _teams(),
            "calendar": _calendar(),
            "driver_standings": [
                {"position": str(i + 1), "points": 100.0 - i, "wins": 0, "driverId": f"d{i:02d}", "teamId": "t0"}
                for i in range(6)
            ],
            "constructor_standings": [
                {"position": "1", "points": 310.0, "wins": 0, "teamId": "red_bull"},
            ],
            "race": _race_payload(drv, 1),
            "qualy": _qualy_payload(drv, 1),
        }
        engine = _db_engine(tmp_path)
        session_factory = _session_factory(engine)
        await _init_db(engine)
        try:
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                summary = await sync.sync_season(2026)
                await session.commit()
                status = (
                    await session.execute(select(Race).where(Race.id == "2026_1"))
                ).scalar_one().status
            assert summary == {
                "season": 2026,
                "calendar": {"season": 2026, "races": 4},
                "grid": {"drivers": 6, "teams": 6},
                "standings": {"drivers": 6, "constructors": 1},
                "results": 6,
                "qualifying": 6,
            }
            assert status == "completed"
        finally:
            await engine.dispose()
    @pytest.mark.asyncio
    async def test_sync_season_stops_before_future_events(self, tmp_path):
        from datetime import date, timedelta
        drv = _drivers(6)
        state = {
            "drivers": drv,
            "teams": _teams(),
            "calendar": _calendar(),
            "driver_standings": [
                {"position": str(i + 1), "points": 100.0 - i, "wins": 0, "driverId": f"d{i:02d}", "teamId": "t0"}
                for i in range(6)
            ],
            "constructor_standings": [
                {"position": "1", "points": 310.0, "wins": 0, "teamId": "red_bull"},
            ],
            "race": _race_payload(drv, 1),
            "qualy": _qualy_payload(drv, 1),
        }
        # Rounds 2-4 are scheduled AFTER "today", so the season must leave
        # them alone (round 1 has a past date and gets synced).
        future = str(date.today() + timedelta(days=60))
        for idx in (1, 2, 3):
            state["calendar"]["races"][idx]["schedule"]["race"]["date"] = future
        engine = _db_engine(tmp_path)
        session_factory = _session_factory(engine)
        await _init_db(engine)
        try:
            async with session_factory() as session:
                sync = F1ApiSync(session, client=FakeClient(state))
                summary = await sync.sync_season(2026)
                await session.commit()
                status = (
                    await session.execute(select(Race).where(Race.id == "2026_2"))
                ).scalar_one().status
            assert summary == {
                "season": 2026,
                "calendar": {"season": 2026, "races": 4},
                "grid": {"drivers": 6, "teams": 6},
                "standings": {"drivers": 6, "constructors": 1},
                "results": 6,
                "qualifying": 6,
            }
            assert status == "scheduled"
        finally:
            await engine.dispose()
