from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class WeatherObservation(Base, UUIDPrimaryKey):
    __tablename__ = "weather_observations"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    session_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    source_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    temperature_c: Mapped[Optional[float]] = mapped_column(nullable=True)
    feels_like_c: Mapped[Optional[float]] = mapped_column(nullable=True)
    humidity_pct: Mapped[Optional[float]] = mapped_column(nullable=True)
    pressure_hpa: Mapped[Optional[float]] = mapped_column(nullable=True)
    precipitation_mm: Mapped[Optional[float]] = mapped_column(nullable=True)
    precipitation_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    wind_speed_ms: Mapped[Optional[float]] = mapped_column(nullable=True)
    wind_gust_ms: Mapped[Optional[float]] = mapped_column(nullable=True)
    wind_direction_deg: Mapped[Optional[float]] = mapped_column(nullable=True)
    cloud_cover_pct: Mapped[Optional[float]] = mapped_column(nullable=True)
    weather_code: Mapped[Optional[int]] = mapped_column(nullable=True)
    track_temp_c: Mapped[Optional[float]] = mapped_column(nullable=True)
    is_wet: Mapped[bool] = mapped_column(default=False, nullable=False)

    race: Mapped["Race"] = relationship("Race", back_populates="weather_observations")
