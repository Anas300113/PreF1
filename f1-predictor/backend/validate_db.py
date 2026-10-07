"""Validate f1api DB state (2026)."""
from app.database import AsyncSessionLocal
from app.models import Race, Driver, Team, RaceResult, QualifyingResult, ChampionshipStanding, DriverTeamSeason
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as s:
        n = await s.scalar(select(Race.season_year).where(Race.season_year == 2026).limit(1))
        print("2026 season row exists:", n)
        rows = (await s.execute(select(Race).where(Race.season_year == 2026).order_by(Race.round_number))).scalars().all()
        print("2026 race rows:", len(rows))
        for r in rows[:5]:
            print("  ", r.round_number, r.race_date, "sprint" if r.is_sprint_weekend else "-", r.status, r.circuit_id)
        print("    ...")
        for r in rows[-3:]:
            print("  ", r.round_number, r.race_date, "sprint" if r.is_sprint_weekend else "-", r.status, r.circuit_id)
        drvs = (await s.execute(select(Driver))).scalars().all()
        teams = (await s.execute(select(Team))).scalars().all()
        print("drivers:", len(drvs), "teams:", len(teams))
        for d in drvs[:2]:
            print("  driver:", d.id, d.first_name, d.last_name, "number:", d.number, "code:", d.code)
        for t in teams[:2]:
            print("  team:", t.id, t.name)
        rr = (await s.execute(select(RaceResult))).scalars().all()
        print("race_results rows:", len(rr))
        if rr:
            print("  sample:", rr[0].race_id, rr[0].driver_id, rr[0].finish_position, rr[0].points, rr[0].source)
        print("  sources:", sorted({r.source for r in rr}))
        ch = (await s.execute(select(ChampionshipStanding))).scalars().all()
        print("championship rows:", len(ch))
        for c in ch[:14]:
            print("  ", c.season, c.entity_type, c.entity_id, c.position, round(c.points, 1))
        dts = (await s.execute(select(DriverTeamSeason))).scalars().all()
        print("driver_team_season rows:", len(dts), "distinct drivers:", len({d.driver_id for d in dts}))

import asyncio
asyncio.run(main())
