"""Persisted backtest results (real evaluation output, never fabricated)."""
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDPrimaryKey


def utcnow():
    return datetime.now(timezone.utc)


class BacktestSeason(Base, UUIDPrimaryKey):
    __tablename__ = "backtest_seasons"

    season: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(nullable=False)
    training_cutoff: Mapped[str] = mapped_column(nullable=False, default="")
    n_races: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_simulations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    simulation_seed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_metrics: Mapped[str] = mapped_column(nullable=False, default="{}")  # JSON
    baseline_metrics: Mapped[str] = mapped_column(nullable=False, default="{}")  # JSON: name -> summary
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    races: Mapped[list["BacktestRace"]] = relationship(
        back_populates="season_summary", cascade="all, delete-orphan"
    )


class BacktestRace(Base, UUIDPrimaryKey):
    __tablename__ = "backtest_races"

    backtest_season_id: Mapped[str] = mapped_column(
        ForeignKey("backtest_seasons.id"), nullable=False, index=True
    )
    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    race_name: Mapped[str] = mapped_column(nullable=False, default="")
    race_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_metrics: Mapped[str] = mapped_column(nullable=False, default="{}")  # JSON
    baselines: Mapped[str] = mapped_column(nullable=False, default="{}")  # JSON: name -> metrics

    season_summary: Mapped[BacktestSeason] = relationship(back_populates="races")