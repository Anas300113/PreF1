from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class Lap(Base, UUIDPrimaryKey):
    __tablename__ = "laps"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    lap_number: Mapped[int] = mapped_column(nullable=False)
    session_type: Mapped[str] = mapped_column(nullable=False)  # 'race','qualifying','fp1','fp2','fp3'
    lap_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    sector1_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    sector2_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    sector3_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    compound: Mapped[Optional[str]] = mapped_column(nullable=True)
    tyre_life: Mapped[Optional[int]] = mapped_column(nullable=True)
    stint_number: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_personal_best: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    track_status: Mapped[Optional[str]] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(default="fastf1", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("race_id", "driver_id", "lap_number", "session_type"),)
