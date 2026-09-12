from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Season(Base):
    __tablename__ = "seasons"

    year: Mapped[int] = mapped_column(primary_key=True)
    num_races: Mapped[Optional[int]] = mapped_column(nullable=True)
    regulation_era: Mapped[str] = mapped_column(default="2022+", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    races: Mapped[List["Race"]] = relationship("Race", back_populates="season")
