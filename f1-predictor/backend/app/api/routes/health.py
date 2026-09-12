from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_settings
from app.schemas.prediction import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db), settings=Depends(get_settings)):
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        version="1.0.0",
        model_version=settings.model_version,
        db_status=db_status,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
