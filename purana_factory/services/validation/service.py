"""Content validation service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.database.base import JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import (
    ContentRepository,
    EntityRepository,
    JobRepository,
    SourceRepository,
    StoryRepository,
)


@dataclass
class ValidationIssue:
    entity_id: int
    entity_name: str
    issue_type: str
    message: str


@dataclass
class ValidationReport:
    total_entities: int = 0
    valid_entities: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_entities": self.total_entities,
            "valid_entities": self.valid_entities,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "entity_id": i.entity_id,
                    "entity_name": i.entity_name,
                    "issue_type": i.issue_type,
                    "message": i.message,
                }
                for i in self.issues
            ],
        }


class ValidationService:
    MIN_DESCRIPTION_LENGTH = 100

    def __init__(self, session: Session) -> None:
        self.session = session
        self.entities = EntityRepository(session)
        self.content = ContentRepository(session)
        self.stories = StoryRepository(session)
        self.sources = SourceRepository(session)
        self.jobs = JobRepository(session)

    def validate_entity(self, entity: Entity) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        content = self.content.get_for_entity(entity.id)
        if not content:
            issues.append(
                ValidationIssue(entity.id, entity.name, "MISSING_CONTENT", "No entity content found")
            )
        else:
            if not content.description or len(content.description) < self.MIN_DESCRIPTION_LENGTH:
                issues.append(
                    ValidationIssue(
                        entity.id,
                        entity.name,
                        "SHORT_DESCRIPTION",
                        f"Description too short (min {self.MIN_DESCRIPTION_LENGTH} chars)",
                    )
                )
            if not content.short_description:
                issues.append(
                    ValidationIssue(
                        entity.id, entity.name, "MISSING_SHORT_DESC", "Missing short description"
                    )
                )

        sources = self.sources.list_for_entity(entity.id)
        if not sources:
            issues.append(
                ValidationIssue(
                    entity.id, entity.name, "MISSING_SOURCES", "No source references"
                )
            )

        return issues

    def validate_all(self) -> ValidationReport:
        job = self.jobs.create(JobType.VALIDATION)
        self.jobs.mark_running(job)
        report = ValidationReport()
        entities = self.entities.list_all()
        report.total_entities = len(entities)

        for entity in entities:
            entity_issues = self.validate_entity(entity)
            if entity_issues:
                report.issues.extend(entity_issues)
            else:
                report.valid_entities += 1

        self.jobs.mark_completed(job, result=json.dumps(report.to_dict()))
        logger.info(
            "Validation complete: {}/{} valid, {} issues",
            report.valid_entities,
            report.total_entities,
            len(report.issues),
        )
        return report
