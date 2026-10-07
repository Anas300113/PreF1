from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class DatasetProvenance(Base):
    """Phase 5: every synced dataset records source/season/retrievedAt/dataVersion."""
    __tablename__ = "dataset_provenance"

    dataset: Mapped[str] = mapped_column(primary_key=True)  # e.g. calendar:2026
    source: Mapped[str] = mapped_column(nullable=False)      # f1api.dev
    season: Mapped[Optional[int]] = mapped_column(nullable=True)
    event: Mapped[Optional[str]] = mapped_column(nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    data_version: Mapped[str] = mapped_column(default="1.0", nullable=False)
    status: Mapped[str] = mapped_column(default="ok", nullable=False)  # ok | error
    detail: Mapped[Optional[str]] = mapped_column(nullable=True)
