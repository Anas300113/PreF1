from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import UUIDPrimaryKey

def utcnow():
    return datetime.now(timezone.utc)

class TeamFormSnapshot(Base, UUIDPrimaryKey):
    __tablename__ = "team_form_snapshots"

    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    race_id_cutoff: Mapped[str] = mapped_column(nullable=False)
    rolling_5_constructor_points: Mapped[Optional[float]] = mapped_column(nullable=True)
    quali_pace_rank: Mapped[Optional[float]] = mapped_column(nullable=True)
    race_pace_rank: Mapped[Optional[float]] = mapped_column(nullable=True)
    dnf_rate_5: Mapped[Optional[float]] = mapped_column(nullable=True)
    pit_stop_avg_s: Mapped[Optional[float]] = mapped_column(nullable=True)
    tyre_deg_index: Mapped[Optional[float]] = mapped_column(nullable=True)
    reliability_score: Mapped[Optional[float]] = mapped_column(nullable=True)
