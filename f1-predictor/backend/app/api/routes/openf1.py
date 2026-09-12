"""OpenF1 API routes for live telemetry, timing, and session data.

These endpoints proxy the OpenF1 API (https://openf1.org/) and provide
enriched data for the dashboard. No API key required.
Rate limited to 3 req/s, 30 req/min on the free tier.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import get_settings
from app.config import Settings
from app.services.openf1_client import OpenF1Client

router = APIRouter(prefix="/api/openf1", tags=["openf1"])


def _client(settings: Settings) -> OpenF1Client:
    return OpenF1Client(settings)


@router.get("/meetings")
async def list_meetings(
    year: Optional[int] = Query(None),
    country: Optional[str] = Query(None),
    settings=Query(None),
):
    """List race weekends (meetings) from OpenF1."""
    client = _client(settings)
    try:
        return client.get_meetings(year=year, country_name=country)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/sessions")
async def list_sessions(
    meeting_key: Optional[int] = Query(None),
    session_name: Optional[str] = Query(None),
    has_data: Optional[bool] = Query(True),
    settings=Query(None),
):
    """List sessions for a meeting."""
    client = _client(settings)
    try:
        return client.get_sessions(meeting_key=meeting_key, session_name=session_name, has_data=has_data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/laps")
async def get_laps(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
    settings=Query(None),
):
    """Get lap times with sector times, speed traps, and pit status."""
    client = _client(settings)
    try:
        return client.get_laps(session_key=session_key, driver_number=driver_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/pit")
async def get_pit_stops(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
    settings=Query(None),
):
    """Get pit stop data with lane_duration and stop_duration."""
    client = _client(settings)
    try:
        return client.get_pit_stops(session_key=session_key, driver_number=driver_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/stints")
async def get_stints(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
    settings=Query(None),
):
    """Get tyre stint data (compound, stint length, tyre age)."""
    client = _client(settings)
    try:
        return client.get_stints(session_key=session_key, driver_number=driver_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/weather")
async def get_weather(
    meeting_key: int = Query(...),
    settings=Query(None),
):
    """Get weather observations for a meeting."""
    client = _client(settings)
    try:
        return client.get_weather(meeting_key=meeting_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/race_control")
async def get_race_control(
    session_key: int = Query(...),
    flag: Optional[str] = Query(None),
    settings=Query(None),
):
    """Get race control messages (flags, safety car, incidents)."""
    client = _client(settings)
    try:
        return client.get_race_control(session_key=session_key, flag=flag)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/drivers")
async def get_drivers(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
    settings=Query(None),
):
    """Get driver list for a session."""
    client = _client(settings)
    try:
        return client.get_drivers(session_key=session_key, driver_number=driver_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
