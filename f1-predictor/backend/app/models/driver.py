from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import TimestampMixin

class Driver(Base, TimestampMixin):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(nullable=True)
    number: Mapped[Optional[int]] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    nationality: Mapped[Optional[str]] = mapped_column(nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(nullable=True)
