from sqlalchemy import PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class DriverTeamSeason(Base):
    __tablename__ = "driver_team_seasons"

    driver_id: Mapped[str] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)
    season_year: Mapped[int] = mapped_column(ForeignKey("seasons.year"), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("driver_id", "season_year"),)
