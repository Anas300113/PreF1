from datetime import datetime, timezone
from sqlalchemy import PrimaryKeyConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ChampionshipStanding(Base):
    """Official standings (source: f1api.dev), season-scoped."""
    __tablename__ = "championship_standings"

    season: Mapped[int] = mapped_column(nullable=False)
    entity_type: Mapped[str] = mapped_column(nullable=False)   # driver | constructor
    entity_id: Mapped[str] = mapped_column(nullable=False)     # driverId / teamId
    position: Mapped[int] = mapped_column(nullable=False)
    points: Mapped[float] = mapped_column(default=0.0, nullable=False)
    wins: Mapped[int] = mapped_column(default=0, nullable=False)
    source: Mapped[str] = mapped_column(default="f1api.dev", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint("season", "entity_type", "entity_id"),)
