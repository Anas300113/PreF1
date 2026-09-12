import asyncio
from typing import Optional, Any, List, Dict
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging
from app.utils.logging_config import get_logger
from app.utils.cache import DiskCache

logger = get_logger("jolpica_client")

class JolpicaClient:
    BASE_URL = "https://api.jolpi.ca/ergast/f1"
    
    def __init__(self, cache_dir: str = "./data/cache/jolpica", timeout: int = 30, rate_limit: int = 4):
        self.cache = DiskCache(cache_dir, default_ttl_seconds=86400)
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.client = httpx.AsyncClient(timeout=self.timeout, headers={"User-Agent": "PreF1-PredictionPlatform/1.0"})

    async def close(self):
        await self.client.aclose()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{path.strip('/')}.json"
        query_str = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
        cache_key = f"{url}?{query_str}"
        
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        async with self.semaphore:
            data = await self._fetch_with_retry(url, params)
            self.cache.set(cache_key, data)
            await asyncio.sleep(0.25)
            return data

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _paginate(self, path: str, resource_key: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        params = dict(params or {})
        params["limit"] = 100
        params["offset"] = 0
        all_items = []
        
        while True:
            res = await self._get(path, params)
            mr = res.get("MRData", {})
            container = mr.get(resource_key, {})
            
            # Key can be list or dictionary wrapping a list
            items = []
            if isinstance(container, list):
                items = container
            elif isinstance(container, dict):
                # find the array field inside container
                for v in container.values():
                    if isinstance(v, list):
                        items = v
                        break
            
            if not items:
                break
                
            all_items.extend(items)
            total = int(mr.get("total", len(all_items)))
            offset = int(mr.get("offset", 0))
            limit = int(mr.get("limit", 100))
            
            if offset + limit >= total:
                break
            params["offset"] = offset + limit
            
        return all_items

    async def get_seasons(self) -> List[Dict[str, Any]]:
        res = await self._get("seasons", {"limit": 100})
        return res.get("MRData", {}).get("SeasonTable", {}).get("Seasons", [])

    async def get_races(self, year: int) -> List[Dict[str, Any]]:
        res = await self._get(f"{year}", {"limit": 100})
        return res.get("MRData", {}).get("RaceTable", {}).get("Races", [])

    async def get_results(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        res = await self._get(f"{year}/{round_num}/results")
        races = res.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return races[0].get("Results", []) if races else []

    async def get_qualifying(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        res = await self._get(f"{year}/{round_num}/qualifying")
        races = res.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return races[0].get("QualifyingResults", []) if races else []

    async def get_pit_stops(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        res = await self._get(f"{year}/{round_num}/pitstops", {"limit": 100})
        races = res.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        return races[0].get("PitStops", []) if races else []

    async def get_driver_standings(self, year: int) -> List[Dict[str, Any]]:
        res = await self._get(f"{year}/driverstandings")
        tables = res.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        return tables[0].get("DriverStandings", []) if tables else []

    async def get_constructor_standings(self, year: int) -> List[Dict[str, Any]]:
        res = await self._get(f"{year}/constructorstandings")
        tables = res.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        return tables[0].get("ConstructorStandings", []) if tables else []

    async def get_drivers(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        path = f"{year}/drivers" if year else "drivers"
        return await self._paginate(path, "DriverTable")

    async def get_constructors(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        path = f"{year}/constructors" if year else "constructors"
        return await self._paginate(path, "ConstructorTable")

    async def get_circuits(self) -> List[Dict[str, Any]]:
        return await self._paginate("circuits", "CircuitTable")
