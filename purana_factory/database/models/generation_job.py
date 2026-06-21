from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, JobStatus, JobType, TimestampMixin


class GenerationJob(Base, TimestampMixin):
    __tablename__ = "generation_job"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int | None] = mapped_column(
        ForeignKey("entity.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True
    )
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    entity: Mapped["Entity | None"] = relationship(back_populates="generation_jobs")
    logs: Mapped[list["GenerationLog"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class GenerationLog(Base, TimestampMixin):
    __tablename__ = "generation_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("generation_job.id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped["GenerationJob"] = relationship(back_populates="logs")


from purana_factory.database.models.entity import Entity  # noqa: E402
