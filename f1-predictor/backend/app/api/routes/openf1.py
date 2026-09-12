"""OpenF1 API routes for live telemetry, timing, and session data.

These endpoints proxy the OpenF1 API (https://openf1.org/) and provide
enriched data for the dashboard. No API key required.
Rate limited to 3 req/s, 30 req/min on the free tier.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.services.openf1_client import OpenF1AuthError, OpenF1Client

router = APIRouter(prefix="/api/openf1", tags=["openf1"])


def _client() -> OpenF1Client:
    return OpenF1Client(get_settings())


@router.get("/meetings")
async def list_meetings(
    year: Optional[int] = Query(None),
    country: Optional[str] = Query(None),
):
    """List race weekends (meetings) from OpenF1."""
    try:
        return _client().get_meetings(year=year, country_name=country)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/sessions")
async def list_sessions(
    meeting_key: Optional[int] = Query(None),
    session_name: Optional[str] = Query(None),
    has_data: Optional[bool] = Query(True),
):
    """List sessions for a meeting."""
    try:
        return _client().get_sessions(meeting_key=meeting_key, session_name=session_name, has_data=has_data)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/laps")
async def get_laps(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
):
    """Get lap times with sector times, speed traps, and pit status."""
    try:
        return _client().get_laps(session_key=session_key, driver_number=driver_number)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/pit")
async def get_pit_stops(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
):
    """Get pit stop data with lane_duration and stop_duration."""
    try:
        return _client().get_pit_stops(session_key=session_key, driver_number=driver_number)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/stints")
async def get_stints(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
):
    """Get tyre stint data (compound, stint length, tyre age)."""
    try:
        return _client().get_stints(session_key=session_key, driver_number=driver_number)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/weather")
async def get_weather(
    meeting_key: int = Query(...),
):
    """Get weather observations for a meeting."""
    try:
        return _client().get_weather(meeting_key=meeting_key)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/race_control")
async def get_race_control(
    session_key: int = Query(...),
    flag: Optional[str] = Query(None),
):
    """Get race control messages (flags, safety car, incidents)."""
    try:
        return _client().get_race_control(session_key=session_key, flag=flag)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc


@router.get("/drivers")
async def get_drivers(
    session_key: int = Query(...),
    driver_number: Optional[int] = Query(None),
):
    """Get driver list for a session."""
    try:
        return _client().get_drivers(session_key=session_key, driver_number=driver_number)
    except OpenF1AuthError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenF1: {exc}") from exc

