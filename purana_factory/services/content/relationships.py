"""Relationship generation service."""

from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.database.base import JobType, RelationshipType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import EntityRepository, JobRepository, RelationshipRepository
from purana_factory.services.content.prompts import RELATIONSHIPS_PROMPT, SYSTEM_PROMPT
from purana_factory.services.content.schemas import RelationshipsSchema
from purana_factory.services.ollama import OllamaService


class RelationshipService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.entities = EntityRepository(session)
        self.relationships = RelationshipRepository(session)
        self.jobs = JobRepository(session)

    def _resolve_target(self, target_name: str, source_type) -> int | None:
        entity = self.entities.get_by_name(target_name)
        if entity:
            return entity.id
        new_entity = self.entities.create(target_name, source_type)
        return new_entity.id

    def generate(self, entity: Entity) -> RelationshipsSchema:
        job = self.jobs.create(JobType.RELATIONSHIPS, entity_id=entity.id)
        self.jobs.mark_running(job)
        try:
            self.relationships.delete_for_entity(entity.id)
            user_prompt = RELATIONSHIPS_PROMPT.format(name=entity.name)
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, RelationshipsSchema, purpose="content"
            )
            for rel in result.relationships:
                try:
                    rel_type = RelationshipType(rel.relationship_type)
                except ValueError:
                    rel_type = RelationshipType.ASSOCIATED_WITH
                target_id = self._resolve_target(rel.target_name, entity.entity_type)
                if target_id:
                    self.relationships.create(
                        source_entity_id=entity.id,
                        target_entity_id=target_id,
                        relationship_type=rel_type,
                        description=rel.description,
                        source_tradition=rel.source_tradition,
                        source_reference=rel.source_reference,
                    )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.relationships)}))
            logger.info("Generated {} relationships for {}", len(result.relationships), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise
