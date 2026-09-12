from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.models import Driver

router = APIRouter(prefix="/api/drivers", tags=["drivers"])

@router.get("/")
async def list_drivers(db: AsyncSession = Depends(get_db)):
    stmt = select(Driver).order_by(Driver.last_name.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{driver_id}")
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
    return driver
