from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models import Season

router = APIRouter(prefix="/api/seasons", tags=["seasons"])


@router.get("/")
async def list_seasons(db: AsyncSession = Depends(get_db)) -> List[dict]:
    stmt = select(Season).order_by(Season.year.desc())
    seasons = (await db.execute(stmt)).scalars().all()
    return [{"year": s.year, "regulation_era": s.regulation_era} for s in seasons]
