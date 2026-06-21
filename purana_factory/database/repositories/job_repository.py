from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.base import JobStatus, JobType
from purana_factory.database.models.generation_job import GenerationJob, GenerationLog


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        job_type: JobType,
        entity_id: int | None = None,
        language: str | None = None,
        payload: str | None = None,
    ) -> GenerationJob:
        job = GenerationJob(
            entity_id=entity_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            language=language,
            payload=payload,
        )
        self.session.add(job)
        self.session.flush()
        return job

    def get_by_id(self, job_id: int) -> GenerationJob | None:
        return self.session.get(GenerationJob, job_id)

    def list_pending(self, job_type: JobType | None = None, limit: int | None = None) -> list[GenerationJob]:
        stmt = select(GenerationJob).where(
            GenerationJob.status.in_([JobStatus.PENDING, JobStatus.RETRY])
        )
        if job_type:
            stmt = stmt.where(GenerationJob.job_type == job_type)
        stmt = stmt.order_by(GenerationJob.id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())

    def mark_running(self, job: GenerationJob) -> GenerationJob:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self.session.flush()
        return job

    def mark_completed(self, job: GenerationJob, result: str | None = None) -> GenerationJob:
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.result = result
        self.session.flush()
        return job

    def mark_failed(self, job: GenerationJob, error: str, retry: bool = False) -> GenerationJob:
        job.error_message = error
        job.retry_count += 1
        job.status = JobStatus.RETRY if retry else JobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc)
        self.session.flush()
        return job

    def add_log(self, job_id: int, level: str, message: str) -> GenerationLog:
        log = GenerationLog(job_id=job_id, level=level, message=message)
        self.session.add(log)
        self.session.flush()
        return log
