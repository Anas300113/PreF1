"""OpenF1 API client with retry logic, caching, and rate limiting.

OpenF1 provides real-time and historical F1 timing, telemetry, and session
data from 2023 onwards. Free tier: 3 req/s, 30 req/min.
No API key required.

Reference: https://openf1.org/ | https://github.com/br-g/openf1
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Optional

import tenacity
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings
from app.utils.logging_config import get_logger

logger = get_logger("openf1_client")

BASE_URL = "https://api.openf1.org/v1"

# DRS status mapping (from OpenF1 docs)
DRS_STATUS = {
    0: "off", 1: "off", 2: "?", 3: "?", 4: "off", 5: "?", 6: "?", 7: "?",
    8: "off", 9: "?", 10: "?", 11: "?", 12: "eligible", 13: "?",
    14: "?", 15: "on",
}

# Session type mapping
SESSION_TYPES = {
    "FP1": "practice_1", "FP2": "practice_2", "FP3": "practice_3",
    "Sprint Qualifying": "sprint_qualifying", "Sprint": "sprint",
    "Qualifying": "qualifying", "Race": "race",
}


class OpenF1Error(Exception):
    """Custom exception for OpenF1 API errors."""


class OpenF1AuthError(OpenF1Error):
    """Raised when authentication is required but missing/invalid."""


class OpenF1Client:
    """Client for the OpenF1 REST API.

    Endpoints:
        /meetings, /sessions, /drivers, /laps, /pit, /stints,
        /position, /intervals, /car_data, /location, /weather,
        /race_control, /team_radio
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._api_key = os.environ.get("OPENF1_API_KEY", "")
        self._last_request_time: float = 0.0
        self._min_interval: float = 1.0 / 3.5  # ~285ms between requests

    @property
    def is_authenticated(self) -> bool:
        """Check if an API key is configured."""
        return bool(self._api_key)

    def _rate_limit(self) -> None:
        """Enforce rate limit between requests."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.monotonic()

    @tenacity.retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((OpenF1Error, OSError, TimeoutError)),
        reraise=True,
    )
    def _request(self, path: str, params: Optional[dict] = None) -> list[dict]:
        """Make a GET request to the OpenF1 API with retry and rate limiting."""
        self._rate_limit()

        url = f"{BASE_URL}/{path}"
        if params:
            query = urllib.parse.urlencode({k: str(v) for k, v in params.items() if v is not None})
            url = f"{url}?{query}"

        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
            headers["x-api-key"] = self._api_key

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not isinstance(data, list):
                    data = [data] if isinstance(data, dict) else []
                return data
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                logger.warning("Rate limited by OpenF1, backing off")
                raise OpenF1Error(f"Rate limited: {exc}") from exc
            if exc.code == 404:
                return []
            if exc.code == 401:
                logger.warning("OpenF1 authentication required (401)")
                raise OpenF1AuthError(
                    "OpenF1 API requires authentication. "
                    "Set OPENF1_API_KEY environment variable. "
                    "See https://openf1.org/ for access details."
                ) from exc
            raise OpenF1Error(f"HTTP {exc.code} for {url}: {exc}") from exc
        except urllib.error.URLError as exc:
            raise OpenF1Error(f"URL error for {url}: {exc}") from exc

    # --- Meetings ---
    def get_meetings(
        self,
        year: Optional[int] = None,
        country_name: Optional[str] = None,
        meeting_key: Optional[int] = None,
        meeting_name: Optional[str] = None,
    ) -> list[dict]:
        """Get race weekends (meetings)."""
        params: dict[str, Any] = {}
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if year is not None:
            params["year"] = year
        if country_name is not None:
            params["country_name"] = country_name
        if meeting_name is not None:
            params["meeting_name"] = meeting_name
        return self._request("meetings", params)

    def get_latest_meeting(self) -> dict | None:
        """Get the most recent or current meeting."""
        results = self._request("meetings", {"meeting_key": "latest"})
        return results[0] if results else None

    # --- Sessions ---
    def get_sessions(
        self,
        meeting_key: Optional[int] = None,
        session_name: Optional[str] = None,
        session_key: Optional[int] = None,
        has_data: Optional[bool] = None,
    ) -> list[dict]:
        """Get sessions for a meeting."""
        params: dict[str, Any] = {}
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if session_name is not None:
            params["session_name"] = session_name
        if session_key is not None:
            params["session_key"] = session_key
        if has_data is not None:
            params["has_data"] = str(has_data).lower()
        return self._request("sessions", params)

    # --- Drivers ---
    def get_drivers(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
    ) -> list[dict]:
        """Get driver list for a session."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._request("drivers", params)

    # --- Laps ---
    def get_laps(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None,
    ) -> list[dict]:
        """Get lap times with sector times, speed traps, and pit status."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if lap_number is not None:
            params["lap_number"] = lap_number
        return self._request("laps", params)

    # --- Pit Stops ---
    def get_pit_stops(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
    ) -> list[dict]:
        """Get pit stop data with lane_duration and stop_duration."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._request("pit", params)

    # --- Stints ---
    def get_stints(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        stint_number: Optional[int] = None,
        tyre_compound: Optional[str] = None,
    ) -> list[dict]:
        """Get tyre stint data (compound, stint length, tyre age)."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if stint_number is not None:
            params["stint_number"] = stint_number
        if tyre_compound is not None:
            params["tyre_compound"] = tyre_compound
        return self._request("stints", params)

    # --- Position ---
    def get_position(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        """Get driver positions over time."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if date is not None:
            params["date"] = date
        return self._request("position", params)

    # --- Intervals ---
    def get_intervals(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
    ) -> list[dict]:
        """Get gap to leader over time."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return self._request("intervals", params)

    # --- Weather ---
    def get_weather(
        self,
        meeting_key: int,
    ) -> list[dict]:
        """Get weather observations for a meeting."""
        return self._request("weather", {"meeting_key": meeting_key})

    # --- Race Control ---
    def get_race_control(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        flag: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        """Get race control messages (flags, SC, incidents)."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if flag is not None:
            params["flag"] = flag
        if date is not None:
            params["date"] = date
        return self._request("race_control", params)

    # --- Car Data (sample, use sparingly — 3.7 Hz) ---
    def get_car_data(
        self,
        session_key: int,
        driver_number: int,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get car telemetry (speed, throttle, brake, RPM, gear, DRS).

        WARNING: 3.7 Hz sampling rate. Use date range filters to avoid
        downloading enormous datasets.
        """
        params: dict[str, Any] = {"session_key": session_key, "driver_number": driver_number}
        if date_start is not None:
            params["date>"] = date_start
        if date_end is not None:
            params["date<"] = date_end
        params["limit"] = str(limit)
        return self._request("car_data", params)

    # --- Location (sample, use sparingly) ---
    def get_location(
        self,
        session_key: int,
        driver_number: int,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get GPS location data."""
        params: dict[str, Any] = {"session_key": session_key, "driver_number": driver_number}
        if date_start is not None:
            params["date>"] = date_start
        if date_end is not None:
            params["date<"] = date_end
        params["limit"] = str(limit)
        return self._request("location", params)
