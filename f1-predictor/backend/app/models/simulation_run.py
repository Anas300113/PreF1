from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class SimulationRun(Base, UUIDPrimaryKey):
    __tablename__ = "simulation_runs"

    prediction_id: Mapped[Optional[str]] = mapped_column(ForeignKey("predictions.id"), nullable=True)
    seed: Mapped[int] = mapped_column(nullable=False)
    n_simulations: Mapped[int] = mapped_column(nullable=False)
    runtime_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=True)
    parameters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
