"""Tests for the OpenF1 API client."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.services.openf1_client import (
    BASE_URL,
    DRS_STATUS,
    OpenF1Client,
    OpenF1Error,
)


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.openf1_enabled = True
    return settings


@pytest.fixture
def client(mock_settings):
    return OpenF1Client(mock_settings)


class TestOpenF1ClientInit:
    def test_base_url_is_correct(self):
        assert BASE_URL == "https://api.openf1.org/v1"

    def test_client_initializes_with_settings(self, client, mock_settings):
        assert client.settings is mock_settings
        assert client._min_interval > 0


class TestDRSStatusMapping:
    def test_drs_off_values(self):
        assert DRS_STATUS[0] == "off"
        assert DRS_STATUS[1] == "off"
        assert DRS_STATUS[4] == "off"
        assert DRS_STATUS[8] == "off"

    def test_drs_on_value(self):
        assert DRS_STATUS[15] == "on"

    def test_drs_eligible_value(self):
        assert DRS_STATUS[12] == "eligible"

    def test_drs_maybe_values(self):
        assert DRS_STATUS[2] == "?"
        assert DRS_STATUS[5] == "?"
        assert DRS_STATUS[14] == "?"


class TestRequest:
    def test_successful_request_returns_list(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"session_key": 9877, "session_name": "Race"}
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client._request("sessions", {"session_key": 9877})

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["session_key"] == 9877

    def test_empty_response_returns_empty_list(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = b"[]"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client._request("laps", {"session_key": 99999})

        assert result == []

    def test_404_returns_empty_list(self, client):
        error = urllib.error.HTTPError(
            url="https://api.openf1.org/v1/laps", code=404,
            msg="Not Found", hdrs={}, fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=error):
            result = client._request("laps", {"session_key": 99999})
        assert result == []

    def test_429_raises_openf1_error(self, client):
        error = urllib.error.HTTPError(
            url="https://api.openf1.org/v1/laps", code=429,
            msg="Too Many Requests", hdrs={}, fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=error):
            with pytest.raises(OpenF1Error, match="Rate limited"):
                client._request("laps", {"session_key": 1})


class TestGetMeetings:
    def test_get_meetings_by_year(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"meeting_key": 1262, "meeting_name": "Spanish Grand Prix", "year": 2026}
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_meetings(year=2026)

        assert len(result) == 1
        assert result[0]["meeting_name"] == "Spanish Grand Prix"

    def test_get_latest_meeting(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"meeting_key": 1262, "meeting_name": "Spanish Grand Prix"}
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_latest_meeting()

        assert result is not None
        assert result["meeting_key"] == 1262


class TestGetSessions:
    def test_get_sessions_by_meeting(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"session_key": 9877, "session_name": "Race", "meeting_key": 1262},
            {"session_key": 9876, "session_name": "Qualifying", "meeting_key": 1262},
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_sessions(meeting_key=1262)

        assert len(result) == 2


class TestGetLaps:
    def test_get_laps_returns_lap_data(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "session_key": 9877, "driver_number": 44, "lap_number": 1,
                "lap_duration": 92.123, "sector_1_time": 28.456,
                "sector_2_time": 35.789, "sector_3_time": 27.878,
                "top_speed": 330, "is_pit_out_lap": False, "deleted": False,
            }
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_laps(session_key=9877, driver_number=44)

        assert len(result) == 1
        assert result[0]["driver_number"] == 44
        assert result[0]["lap_duration"] == 92.123


class TestGetStints:
    def test_get_stints_returns_stint_data(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "session_key": 9877, "driver_number": 44, "stint_number": 1,
                "tyre_compound": "SOFT", "tyre_age_at_start": 0,
                "lap_start": 1, "lap_end": 20,
            }
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_stints(session_key=9877, driver_number=44)

        assert len(result) == 1
        assert result[0]["tyre_compound"] == "SOFT"


class TestGetPitStops:
    def test_get_pit_stops_returns_pit_data(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "session_key": 9877, "driver_number": 44,
                "lap_number": 20, "lane_duration": 22.5, "stop_duration": 2.3,
            }
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_pit_stops(session_key=9877, driver_number=44)

        assert len(result) == 1
        assert result[0]["lane_duration"] == 22.5


class TestGetWeather:
    def test_get_weather_returns_weather_data(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "meeting_key": 1262, "air_temperature": 28.9,
                "track_temperature": 42.1, "humidity": 45.0,
                "wind_speed": 3.2, "rainfall": 0,
            }
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_weather(meeting_key=1262)

        assert len(result) == 1
        assert result[0]["air_temperature"] == 28.9
        assert result[0]["rainfall"] == 0


class TestGetRaceControl:
    def test_get_race_control_returns_messages(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "session_key": 9877, "message": "YELLOW FLAG - TURN 3",
                "flag": "YELLOW", "scope": "sector", "sector": 3,
            }
        ]).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get_race_control(session_key=9877)

        assert len(result) == 1
        assert result[0]["flag"] == "YELLOW"
