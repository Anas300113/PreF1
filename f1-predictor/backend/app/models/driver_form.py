from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class DriverFormSnapshot(Base, UUIDPrimaryKey):
    __tablename__ = "driver_form_snapshots"

    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    race_id_cutoff: Mapped[str] = mapped_column(nullable=False)
    rolling_3_finish: Mapped[Optional[float]] = mapped_column(nullable=True)
    rolling_5_finish: Mapped[Optional[float]] = mapped_column(nullable=True)
    rolling_10_finish: Mapped[Optional[float]] = mapped_column(nullable=True)
    rolling_3_points: Mapped[Optional[float]] = mapped_column(nullable=True)
    rolling_5_points: Mapped[Optional[float]] = mapped_column(nullable=True)
    dnf_rate_10: Mapped[Optional[float]] = mapped_column(nullable=True)
    quali_vs_teammate_3: Mapped[Optional[float]] = mapped_column(nullable=True)
    race_vs_teammate_3: Mapped[Optional[float]] = mapped_column(nullable=True)
    podium_rate_10: Mapped[Optional[float]] = mapped_column(nullable=True)
    overtaking_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    wet_weather_delta: Mapped[Optional[float]] = mapped_column(nullable=True)
    street_circuit_delta: Mapped[Optional[float]] = mapped_column(nullable=True)
    circuit_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    circuit_avg_finish: Mapped[Optional[float]] = mapped_column(nullable=True)
