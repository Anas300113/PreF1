"""Unit tests for f1api.dev HTTP client (caching, errors, pagination)."""
from unittest.mock import patch

import pytest

from app.services.f1api.client import F1ApiClient, F1ApiError

BASE = "https://f1api.dev"


class TestGetCache:
    @pytest.mark.asyncio
    async def test_returns_cached_result_without_refetch(self, tmp_path):
        client = F1ApiClient(cache_dir=str(tmp_path))
        key = f"{BASE}/api/2026"
        expected = {"season": 2026, "races": []}

        with patch.object(client, "_fetch", return_value=expected):
            first = await client.get(key, ttl=60)
            second = await client.get(key, ttl=60)

        assert first == second == expected
        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_cached_result_unchanged_across_calls(self, tmp_path):
        client = F1ApiClient(cache_dir=str(tmp_path))
        key = f"{BASE}/api/2026/drivers"
        payload = {"drivers": [{"driverId": "max_verstappen"}]}

        with patch.object(client, "_fetch", return_value=payload):
            await client.get(key, ttl=60)
            await client.get(key, ttl=60)

        assert len(list(tmp_path.glob("*.json"))) == 1


class TestFetchErrorHandling:
    @pytest.mark.asyncio
    async def test_http_error_wrapped(self, tmp_path):
        client = F1ApiClient(cache_dir=str(tmp_path))

        with patch.object(client, "_fetch", side_effect=RuntimeError("network down")):
            with pytest.raises(F1ApiError, match="f1api.dev unavailable"):
                await client.get(f"{BASE}/api/2026", ttl=60)

    @pytest.mark.asyncio
    async def test_404_raised(self, tmp_path):
        client = F1ApiClient(cache_dir=str(tmp_path))

        with patch.object(
            client, "_fetch", side_effect=F1ApiError(f"404 from f1api.dev: {BASE}/api/2026")
        ):
            with pytest.raises(F1ApiError, match="404"):
                await client.get(f"{BASE}/api/2026", ttl=60)


class TestPaged:
    @pytest.mark.asyncio
    async def test_pagination_until_total(self, tmp_path):
        client = F1ApiClient(cache_dir=str(tmp_path))
        pages = [
            {"drivers": [{"driverId": f"d{i}"} for i in range(100)], "total": 250},
            {"drivers": [{"driverId": f"d{i}"} for i in range(100, 250)], "total": 250},
            {"drivers": [], "total": 250},
        ]

        with patch.object(client, "_fetch", side_effect=pages):
            items = await client.paged(f"{BASE}/api/2026/drivers", "drivers", ttl=60)

        assert [i["driverId"] for i in items] == [f"d{i}" for i in range(250)]

    @pytest.mark.asyncio
    async def test_stops_on_empty_chunk(self, tmp_path):
        client = F1ApiClient(cache_dir=str(tmp_path))

        with patch.object(client, "_fetch", return_value={"drivers": []}):
            items = await client.paged(f"{BASE}/api/2026/drivers", "drivers", ttl=60)

        assert items == []
