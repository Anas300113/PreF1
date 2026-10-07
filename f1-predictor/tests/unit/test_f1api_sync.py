"""End-to-end tests for the f1api.dev sync service against a throwaway DB.

Runs completely offline: the HTTP client is replaced by a canned payload
provider, and SQLAlchemy points at a temporary SQLite file.
"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Repo-level conftest puts `backend` on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database import Base  # noqa: E402
from app.models import (  # noqa: E402
    ChampionshipStanding,
    Driver,
    DriverTeamSeason,
    QualifyingResult,
    Race,
    RaceResult,
    Season,
    Team,
)
from app.services.f1api.sync import F1ApiSync  # noqa: E402


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
    """4 races: round 2 is a sprint; round 4 is in the future."""
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
            race["schedule"]["sprintRace"] = {"date": f"2026-03-14", "time": "12:00"}
        races.append(race)
    return {"season": 2026, "races": races}





