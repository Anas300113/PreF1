from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class QualifyingResult(Base, UUIDPrimaryKey):
    __tablename__ = "qualifying_results"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    position: Mapped[Optional[int]] = mapped_column(nullable=True)
    q1_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    q2_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    q3_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    best_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    gap_to_pole_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    relative_pace: Mapped[Optional[float]] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(default="jolpica", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    race: Mapped["Race"] = relationship("Race", back_populates="qualifying_results")
    driver: Mapped["Driver"] = relationship("Driver")
