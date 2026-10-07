"""One-shot: sync a season from f1api.dev into the local DB. Usage: python sync_f1api.py [year]"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal, init_db
from app.services.f1api.sync import F1ApiSync


async def main(year: int):
    await init_db()
    async with AsyncSessionLocal() as session:
        sync = F1ApiSync(session)
        try:
            summary = await sync.sync_season(year, include_events=True)
            print("SYNC OK:", summary)
        finally:
            await sync.close()


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2026))
