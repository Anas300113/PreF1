from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_settings
from app.schemas.prediction import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
):
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    # Model artifact verification status (set during startup lifespan).
    model_status: Optional[Dict[str, Any]] = getattr(request.app.state, "model_status", None)
    if model_status is None:
        from app.ml.model_registry import ModelRegistry
        model_status = ModelRegistry(settings.models_dir).load_status(
            settings.required_model_list()
        )
    models_ok = bool(model_status.get("all_available", False))

    status = "ok"
    if db_status != "healthy" or not models_ok:
        status = "degraded"

    return HealthResponse(
        status=status,
        version="1.0.0",
        model_version=settings.model_version,
        db_status=db_status,
        models_available=models_ok,
        models=model_status.get("models", {}),
        timestamp=datetime.now(timezone.utc).isoformat()
    )
