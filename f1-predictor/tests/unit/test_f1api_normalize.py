"""Unit tests for f1api.dev normalization helpers."""
import pytest

from app.services.f1api.normalize import parse_float, parse_int, parse_lap_time
from app.services.f1api.normalize import parse_lap_time as parse_race_time


class TestParseInt:
    def test_returns_int(self):
        assert parse_int("1") == 1
        assert parse_int("0") == 0

    def test_none_returns_none(self):
        assert parse_int(None) is None

    def test_empty_returns_none(self):
        assert parse_int("") is None

    def test_invalid_returns_none(self):
        assert parse_int("abc") is None

    def test_whitespace_handled(self):
        assert parse_int("  42  ") == 42


class TestParseFloat:
    def test_returns_float(self):
        assert parse_float("25.5") == 25.5
        assert parse_float("12") == 12.0

    def test_none_returns_none(self):
        assert parse_float(None) is None

    def test_kmh_with_unit(self):
        assert parse_float("320 km/h".replace("km/h", "").strip()) == 320.0

    def test_invalid_returns_none(self):
        assert parse_float("abc") is None


class TestParseLapTime:
    def test_hms(self):
        assert parse_lap_time("1:35.867") == pytest.approx(95.867)
        assert parse_lap_time("1:30:12.345") == pytest.approx(5412.345)

    def test_seconds_string(self):
        assert parse_lap_time("95.867") == pytest.approx(95.867)

    def test_null_returns_none(self):
        assert parse_lap_time(None) is None
        assert parse_lap_time("") is None

    def test_invalid_returns_none(self):
        assert parse_lap_time("not-a-time") is None



class TestParseRaceTime:
    def test_returns_seconds_for_hms(self):
        assert parse_lap_time("1:30:12.345") == pytest.approx(5412.345)
        assert parse_race_time("1:30:12.345") == pytest.approx(5412.345)

    def test_null_returns_none(self):
        assert parse_race_time(None) is None
        assert parse_race_time("") is None

    def test_invalid_returns_none(self):
        assert parse_race_time("fastest") is None
