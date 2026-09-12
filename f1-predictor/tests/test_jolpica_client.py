import pytest
from unittest.mock import AsyncMock, patch

from app.services.jolpica_client import JolpicaClient


@pytest.mark.asyncio
async def test_jolpica_get_seasons_parses_response():
    client = JolpicaClient(cache_dir="./data/cache/jolpica_test")
    mock_response = {
        "MRData": {
            "SeasonTable": {
                "Seasons": [{"season": "2024"}, {"season": "2023"}]
            }
        }
    }
    with patch.object(client, "_get", new=AsyncMock(return_value=mock_response)):
        seasons = await client.get_seasons()
    assert len(seasons) == 2
    assert seasons[0]["season"] == "2024"
    await client.close()


@pytest.mark.asyncio
async def test_jolpica_get_results_empty():
    client = JolpicaClient(cache_dir="./data/cache/jolpica_test")
    mock_response = {"MRData": {"RaceTable": {"Races": []}}}
    with patch.object(client, "_get", new=AsyncMock(return_value=mock_response)):
        results = await client.get_results(2024, 1)
    assert results == []
    await client.close()
