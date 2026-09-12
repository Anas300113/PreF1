from sqlalchemy import PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class RaceEntry(Base):
    __tablename__ = "race_entries"

    race_id: Mapped[str] = mapped_column(ForeignKey("races.id"), nullable=False)
    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("race_id", "driver_id"),)
