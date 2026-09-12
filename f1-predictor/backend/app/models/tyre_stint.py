from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import UUIDPrimaryKey

class TyreStint(Base, UUIDPrimaryKey):
    __tablename__ = "tyre_stints"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    stint_number: Mapped[int] = mapped_column(nullable=False)
    compound: Mapped[Optional[str]] = mapped_column(nullable=True)
    start_lap: Mapped[int] = mapped_column(nullable=False)
    end_lap: Mapped[Optional[int]] = mapped_column(nullable=True)
    stint_length: Mapped[Optional[int]] = mapped_column(nullable=True)
    avg_pace_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    pace_degradation_s_per_lap: Mapped[Optional[float]] = mapped_column(nullable=True)
    cliff_detected: Mapped[bool] = mapped_column(default=False, nullable=False)
    source: Mapped[str] = mapped_column(default="fastf1", nullable=False)
