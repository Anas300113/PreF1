from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin

class Circuit(Base, TimestampMixin):
    __tablename__ = "circuits"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[Optional[str]] = mapped_column(nullable=True)
    locality: Mapped[Optional[str]] = mapped_column(nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    altitude_m: Mapped[Optional[float]] = mapped_column(nullable=True)
    length_km: Mapped[Optional[float]] = mapped_column(nullable=True)
    lap_record_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    num_corners: Mapped[Optional[int]] = mapped_column(nullable=True)
    avg_corner_speed_kmh: Mapped[Optional[float]] = mapped_column(nullable=True)
    high_speed_corner_pct: Mapped[Optional[float]] = mapped_column(nullable=True)
    straight_length_m: Mapped[Optional[float]] = mapped_column(nullable=True)
    braking_intensity: Mapped[Optional[float]] = mapped_column(nullable=True)
    overtaking_difficulty: Mapped[Optional[float]] = mapped_column(nullable=True)
    pit_loss_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    tyre_degradation_index: Mapped[Optional[float]] = mapped_column(nullable=True)
    safety_car_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    circuit_type: Mapped[Optional[str]] = mapped_column(nullable=True)

    races: Mapped[List["Race"]] = relationship("Race", back_populates="circuit")
