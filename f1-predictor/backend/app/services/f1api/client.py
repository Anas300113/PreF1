"""f1api.dev client — the single entry point for external F1 data.

Endpoints follow the published OpenAPI spec (Rafacv23/F1-api, openapi.yaml):
  /api/current, /api/current/next, /api/current/drivers,
  /api/{year}, /api/{year}/drivers, /api/{year}/drivers-championship,
  /api/{year}/constructors-championship, /api/{year}/{round}/race,
  /api/{year}/{round}/qualy, /api/{year}/{round}/sprint/race,
  /api/{year}/{round}/sprint/qualy, /api/{year}/compare/{d1}/{d2}

Caching policy (Phase 20) — TTLs by data volatility:
  historical results/quali -> 7 days
  season calendar          -> 6 hours
  standings / grid / next  -> 15 minutes
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.utils.cache import DiskCache

logger = logging.getLogger("f1api_client")

BASE_URL = "https://f1api.dev"

TTL_HISTORICAL = 7 * 24 * 3600
TTL_CALENDAR = 6 * 3600
TTL_STANDINGS = 15 * 60


class F1ApiError(Exception):
    """Raised when f1api.dev is unavailable or returns an invalid payload."""


class F1ApiClient:
    def __init__(self, cache_dir: str = "./data/cache/f1api", timeout: int = 30):
        self.cache = DiskCache(cache_dir, default_ttl_seconds=TTL_CALENDAR)
        self.timeout = timeout
        self._sem = asyncio.Semaphore(4)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "PreF1/2.0 (race intelligence product)"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.5, min=1, max=20),
        retry=retry_if_exception_type((httpx.HTTPError,)),
        before_sleep=before_sleep_log(logger, 20),
    )
    async def _fetch(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        client = await self._get_client()
        async with self._sem:
            resp = await client.get(f"{BASE_URL}{path}", params=params)
        if resp.status_code == 404:
            raise F1ApiError(f"404 from f1api.dev: {path}")
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise F1ApiError(f"Unexpected payload from f1api.dev: {path}")
        return data

    async def get(
        self, path: str, params: Optional[Dict[str, Any]] = None, ttl: int = TTL_CALENDAR
    ) -> Dict[str, Any]:
        """Cached GET with retry. Raises F1ApiError when unavailable and uncached."""
        params = params or {}
        key = f"{BASE_URL}{path}?{'&'.join(f'{k}={v}' for k, v in sorted(params.items()))}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        try:
            data = await self._fetch(path, params)
        except Exception as exc:
            raise F1ApiError(f"f1api.dev unavailable for {path}: {exc}") from exc
        self.cache.set(key, data, ttl_seconds=ttl)
        return data

    async def paged(
        self, path: str, resource_key: str, ttl: int, extra: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all items for list endpoints (limit max 100 per spec)."""
        items: List[Dict[str, Any]] = []
        offset = 0
        extra = extra or {}
        while True:
            params = {"limit": 100, "offset": offset, **extra}
            data = await self.get(path, params, ttl=ttl)
            chunk = data.get(resource_key)
            if not isinstance(chunk, list) or not chunk:
                break
            items.extend(chunk)
            total = int(data.get("total") or len(items))
            offset += len(chunk)
            if offset >= total or offset >= 10000:
                break
            await asyncio.sleep(0.2)
        return items

    # ---------------------- Season / calendar ------------------------- #
    async def season_calendar(self, year: Optional[int] = None) -> Dict[str, Any]:
        path = "/api/current" if year is None else f"/api/{year}"
        return await self.get(path, {"limit": 100}, ttl=TTL_CALENDAR)

    async def next_race(self) -> Dict[str, Any]:
        return await self.get("/api/current/next", {"limit": 10}, ttl=TTL_STANDINGS)

    # ---------------- Grid / standings (season-scoped) ---------------- #
    async def season_drivers(self, year: int) -> List[Dict[str, Any]]:
        return await self.paged(f"/api/{year}/drivers", "drivers", ttl=TTL_STANDINGS)

    async def season_teams(self, year: int) -> List[Dict[str, Any]]:
        return await self.paged(f"/api/{year}/teams", "teams", ttl=TTL_CALENDAR)

    async def drivers_championship(self, year: int) -> List[Dict[str, Any]]:
        return await self.paged(
            f"/api/{year}/drivers-championship", "drivers_championship", ttl=TTL_STANDINGS
        )

    async def constructors_championship(self, year: int) -> List[Dict[str, Any]]:
        return await self.paged(
            f"/api/{year}/constructors-championship",
            "constructors_championship",
            ttl=TTL_STANDINGS,
        )

    # ------------------------- Event data ----------------------------- #
    async def race_results(self, year: int, round_: int) -> Dict[str, Any]:
        return await self.get(f"/api/{year}/{round_}/race", {"limit": 100}, ttl=TTL_HISTORICAL)

    async def qualifying(self, year: int, round_: int) -> Dict[str, Any]:
        return await self.get(f"/api/{year}/{round_}/qualy", {"limit": 100}, ttl=TTL_HISTORICAL)

    async def sprint_race(self, year: int, round_: int) -> Dict[str, Any]:
        return await self.get(
            f"/api/{year}/{round_}/sprint/race", {"limit": 100}, ttl=TTL_HISTORICAL
        )

    async def sprint_qualifying(self, year: int, round_: int) -> Dict[str, Any]:
        return await self.get(
            f"/api/{year}/{round_}/sprint/qualy", {"limit": 100}, ttl=TTL_HISTORICAL
        )

    async def head_to_head(self, year: int, driver1: str, driver2: str) -> Dict[str, Any]:
        return await self.get(
            f"/api/{year}/compare/{driver1}/{driver2}", {"limit": 100}, ttl=TTL_CALENDAR
        )
