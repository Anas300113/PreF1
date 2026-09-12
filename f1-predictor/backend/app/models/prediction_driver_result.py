from typing import Optional
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDPrimaryKey

class PredictionDriverResult(Base, UUIDPrimaryKey):
    __tablename__ = "prediction_driver_results"

    prediction_id: Mapped[str] = mapped_column(ForeignKey("predictions.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    win_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    podium_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    top5_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    top10_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    points_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    dnf_probability: Mapped[Optional[float]] = mapped_column(nullable=True)
    expected_position: Mapped[Optional[float]] = mapped_column(nullable=True)
    median_position: Mapped[Optional[float]] = mapped_column(nullable=True)
    p10_position: Mapped[Optional[float]] = mapped_column(nullable=True)
    p25_position: Mapped[Optional[float]] = mapped_column(nullable=True)
    p75_position: Mapped[Optional[float]] = mapped_column(nullable=True)
    p90_position: Mapped[Optional[float]] = mapped_column(nullable=True)
    expected_points: Mapped[Optional[float]] = mapped_column(nullable=True)
    position_distribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shap_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="driver_results")
    driver: Mapped["Driver"] = relationship("Driver")
