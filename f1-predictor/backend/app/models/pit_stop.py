from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class PitStop(Base, UUIDPrimaryKey):
    __tablename__ = "pit_stops"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    stop_number: Mapped[int] = mapped_column(nullable=False)
    lap: Mapped[int] = mapped_column(nullable=False)
    duration_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    compound_before: Mapped[Optional[str]] = mapped_column(nullable=True)
    compound_after: Mapped[Optional[str]] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(default="jolpica", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("race_id", "driver_id", "stop_number"),)
