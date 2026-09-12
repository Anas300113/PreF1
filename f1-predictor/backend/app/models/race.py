from typing import Optional, List
from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin

class Race(Base, TimestampMixin):
    __tablename__ = "races"

    id: Mapped[str] = mapped_column(primary_key=True)
    season_year: Mapped[int] = mapped_column(ForeignKey("seasons.year"), nullable=False)
    round_number: Mapped[int] = mapped_column(nullable=False)
    circuit_id: Mapped[str] = mapped_column(ForeignKey("circuits.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    official_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    race_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    race_time: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_sprint_weekend: Mapped[bool] = mapped_column(default=False, nullable=False)
    total_laps: Mapped[Optional[int]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(default="scheduled", nullable=False)

    season: Mapped["Season"] = relationship("Season", back_populates="races")
    circuit: Mapped["Circuit"] = relationship("Circuit", back_populates="races")
    qualifying_results: Mapped[List["QualifyingResult"]] = relationship("QualifyingResult", back_populates="race")
    race_results: Mapped[List["RaceResult"]] = relationship("RaceResult", back_populates="race")
    weather_observations: Mapped[List["WeatherObservation"]] = relationship("WeatherObservation", back_populates="race")
