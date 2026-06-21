"""Bootstrap mythology entities."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.database.base import EntityType, JobType
from purana_factory.database.repositories import EntityRepository, JobRepository
from purana_factory.services.bootstrap.entities import BOOTSTRAP_ENTITIES


class BootstrapService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.entities = EntityRepository(session)
        self.jobs = JobRepository(session)

    def load_entities(self) -> tuple[int, int]:
        job = self.jobs.create(JobType.BOOTSTRAP)
        self.jobs.mark_running(job)
        created = 0
        skipped = 0
        try:
            for name, entity_type, sanskrit in BOOTSTRAP_ENTITIES:
                existing = self.entities.get_by_name(name)
                if existing:
                    skipped += 1
                    continue
                self.entities.create(name, entity_type, sanskrit_name=sanskrit)
                created += 1
            self.jobs.mark_completed(job, result=f"created={created},skipped={skipped}")
            logger.info("Bootstrap complete: {} created, {} skipped", created, skipped)
            return created, skipped
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc))
            raise
