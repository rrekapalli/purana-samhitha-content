"""Entity profile content generation."""

from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.database.base import EntityStatus, JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import (
    ContentRepository,
    EntityRepository,
    JobRepository,
    KeywordRepository,
    SourceRepository,
)
from purana_factory.services.content.prompts import ENTITY_PROFILE_PROMPT, SYSTEM_PROMPT
from purana_factory.services.content.schemas import EntityProfileSchema
from purana_factory.services.ollama import OllamaService


def _list_to_text(items: list[str] | None) -> str | None:
    if not items:
        return None
    return "\n".join(f"- {item}" for item in items)


class EntityProfileService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.entities = EntityRepository(session)
        self.content = ContentRepository(session)
        self.keywords = KeywordRepository(session)
        self.sources = SourceRepository(session)
        self.jobs = JobRepository(session)

    def generate(self, entity: Entity, language: str = "en") -> EntityProfileSchema:
        job = self.jobs.create(JobType.ENTITY_PROFILE, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            self.entities.update_status(entity, EntityStatus.IN_PROGRESS)
            user_prompt = ENTITY_PROFILE_PROMPT.format(
                name=entity.name,
                entity_type=entity.entity_type.value,
            )
            profile = self.ollama.generate_validated(
                SYSTEM_PROMPT,
                user_prompt,
                EntityProfileSchema,
                purpose="content",
            )
            if profile.sanskrit_name:
                entity.sanskrit_name = profile.sanskrit_name

            content_data = {
                "aliases": ", ".join(profile.aliases) if profile.aliases else None,
                "description": profile.description,
                "short_description": profile.short_description,
                "iconography": profile.iconography,
                "powers": _list_to_text(profile.powers),
                "abilities": _list_to_text(profile.abilities),
                "boons": _list_to_text(profile.boons),
                "curses": _list_to_text(profile.curses),
                "teachings": _list_to_text(profile.teachings),
                "virtues": _list_to_text(profile.virtues),
                "flaws": _list_to_text(profile.flaws),
                "moral_lessons": _list_to_text(profile.moral_lessons),
            }
            self.content.upsert(entity.id, content_data, language=language)
            self.keywords.delete_for_entity(entity.id)
            self.keywords.add_keywords(entity.id, profile.search_keywords, language=language)
            self.sources.delete_for_entity(entity.id)
            for source in profile.primary_sources:
                scripture = source.split(",")[0].strip() if "," in source else source
                citation = source if "," in source else None
                self.sources.create(entity.id, scripture=scripture, citation=citation)

            self.jobs.mark_completed(job, result=json.dumps({"entity_id": entity.id}))
            self.jobs.add_log(job.id, "INFO", f"Generated profile for {entity.name}")
            logger.info("Generated profile for entity: {}", entity.name)
            return profile
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            self.entities.update_status(entity, EntityStatus.FAILED)
            raise
