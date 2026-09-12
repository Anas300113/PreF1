from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class Prediction(Base, UUIDPrimaryKey):
    __tablename__ = "predictions"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(default="pre_race", nullable=False)
    model_version: Mapped[str] = mapped_column(nullable=False)
    feature_version: Mapped[str] = mapped_column(nullable=False)
    training_cutoff: Mapped[Optional[str]] = mapped_column(nullable=True)
    weather_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    simulation_seed: Mapped[Optional[int]] = mapped_column(nullable=True)
    simulation_count: Mapped[int] = mapped_column(default=10000, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    driver_results: Mapped[List["PredictionDriverResult"]] = relationship("PredictionDriverResult", back_populates="prediction")
