from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.models import Team

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.get("/")
async def list_teams(db: AsyncSession = Depends(get_db)):
    stmt = select(Team).order_by(Team.name.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{team_id}")
async def get_team(team_id: str, db: AsyncSession = Depends(get_db)):
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return team
