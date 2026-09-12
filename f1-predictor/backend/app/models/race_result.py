from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class RaceResult(Base, UUIDPrimaryKey):
    __tablename__ = "race_results"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    grid_position: Mapped[Optional[int]] = mapped_column(nullable=True)
    finish_position: Mapped[Optional[int]] = mapped_column(nullable=True)
    classified: Mapped[bool] = mapped_column(default=True, nullable=False)
    status_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    status_detail: Mapped[Optional[str]] = mapped_column(nullable=True)
    dnf: Mapped[bool] = mapped_column(default=False, nullable=False)
    laps_completed: Mapped[Optional[int]] = mapped_column(nullable=True)
    race_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    gap_to_winner_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    points: Mapped[float] = mapped_column(default=0.0, nullable=False)
    fastest_lap: Mapped[bool] = mapped_column(default=False, nullable=False)
    fastest_lap_time_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    pit_stop_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(default="jolpica", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    race: Mapped["Race"] = relationship("Race", back_populates="race_results")
    driver: Mapped["Driver"] = relationship("Driver")
