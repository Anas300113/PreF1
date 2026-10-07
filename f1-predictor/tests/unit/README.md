# Unit tests

Offline test suite for the f1api.dev integration (`backend/app/services/f1api/`).

## Layout

- `test_f1api_client.py` — HTTP client: disk-cache round trips, error wrapping, pagination.
- `test_f1api_normalize.py` — `parse_int` / `parse_float` / `parse_lap_time` helpers.
- `test_f1api_sync.py` — calendar sync against a throwaway SQLite DB.
- `test_part2b.py` — `F1ApiSync` grid / standings / event / season flows against a
  throwaway SQLite DB, using a canned `FakeClient` (no network).

## Run

From `f1-predictor/`:

```powershell
python -m pytest tests/unit -q -p no:cacheprovider
```

Requirements: `pytest`, `pytest-asyncio` (async tests rely on `asyncio_mode = auto`
from the repo-root `pytest.ini`), `aiosqlite`, `httpx`, `tenacity`, `pydantic`.

## Notes

- `tests/conftest.py` puts `backend/` and `tests/unit/` on `sys.path`.
- Sync tests assert against the real ORM models (`Race`, `RaceResult`,
  `QualifyingResult`, `ChampionshipStanding`, `DatasetProvenance`, …).
- Lap-time asserts use `pytest.approx` (float round-off, e.g. 95.86699999999999).
