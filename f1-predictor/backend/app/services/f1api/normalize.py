"""Validation / normalization for f1api.dev responses.

Every normalized object carries provenance: source, season, retrieved_at,
data_version so the UI can distinguish official vs calculated vs predicted data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

SOURCE = "f1api.dev"
DATA_VERSION = "1.0"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_lap_time(value: Any) -> Optional[float]:
    """Parse '1:36.477' / '1:47:14.808' / 87.31 -> seconds. None/invalid -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s in {"-", "N/A"}:
        return None
    if s.startswith("+"):  # gap marker, not an absolute time
        return None
    try:
        parts = [float(p) for p in s.split(":")]
    except ValueError:
        return None
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 1:
        return parts[0]
    return None


def parse_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def parse_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


class Provenance(BaseModel):
    source: str = SOURCE
    season: Optional[int] = None
    event: Optional[str] = None
    retrieved_at: str = Field(default_factory=utcnow_iso)
    data_version: str = DATA_VERSION
    # LIVE | CURRENT | HISTORICAL | CALCULATED | PREDICTED | ESTIMATED
    freshness: str = "CURRENT"


class NormDriver(BaseModel):
    driver_id: str
    code: Optional[str] = None
    number: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    nationality: Optional[str] = None
    team_id: Optional[str] = None  # season-scoped only; never global
    url: Optional[str] = None


class NormTeam(BaseModel):
    team_id: str
    name: str
    country: Optional[str] = None


class NormCircuit(BaseModel):
    circuit_id: str
    name: str
    country: Optional[str] = None
    city: Optional[str] = None
    length_km: Optional[float] = None
    corners: Optional[int] = None
    lap_record_s: Optional[float] = None

    @field_validator("length_km", mode="before")
    @classmethod
    def _len(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        s = str(v).lower().replace("km", "").strip()
        return parse_float(s)


class NormRace(BaseModel):
    race_id: str            # internal id: {year}_{round}
    season_year: int
    round_number: int
    name: str               # short name e.g. "Singapore Grand Prix"
    official_name: Optional[str] = None
    race_date: Optional[str] = None
    race_time: Optional[str] = None
    laps: Optional[int] = None
    is_sprint: bool = False
    circuit: Optional[NormCircuit] = None
    winner_driver_id: Optional[str] = None
    winner_team_id: Optional[str] = None
    status: str = "scheduled"  # scheduled | completed


class NormResult(BaseModel):
    position: Optional[int] = None
    grid: Optional[int] = None
    points: float = 0.0
    time_s: Optional[float] = None
    gap_to_winner: Optional[str] = None
    fastest_lap_s: Optional[float] = None
    dnf: bool = False
    status: Optional[str] = None
    driver_id: str
    code: Optional[str] = None
    number: Optional[int] = None
    team_id: str


class NormQualiResult(BaseModel):
    position: Optional[int] = None
    grid_position: Optional[int] = None
    q1_s: Optional[float] = None
    q2_s: Optional[float] = None
    q3_s: Optional[float] = None
    driver_id: str
    team_id: str


class NormDriverStanding(BaseModel):
    position: int
    driver_id: str
    team_id: str
    points: float
    wins: int = 0
    code: Optional[str] = None
    number: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nationality: Optional[str] = None


class NormTeamStanding(BaseModel):
    position: int
    team_id: str
    points: float
    wins: int = 0
    name: Optional[str] = None
    country: Optional[str] = None
