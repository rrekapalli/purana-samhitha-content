"""Translation service using Ollama."""

from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.config import get_settings
from purana_factory.database.base import JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import ContentRepository, JobRepository, LanguageRepository
from purana_factory.services.content.prompts import SYSTEM_PROMPT, TRANSLATION_PROMPT
from purana_factory.services.content.schemas import TranslationSchema
from purana_factory.services.ollama import OllamaService

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "sa": "Sanskrit",
}


class TranslationService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.content = ContentRepository(session)
        self.languages = LanguageRepository(session)
        self.jobs = JobRepository(session)
        self.settings = get_settings()

    def translate_entity(self, entity: Entity, target_language: str) -> TranslationSchema:
        if target_language == "en":
            raise ValueError("Cannot translate to source language 'en'")

        job = self.jobs.create(
            JobType.TRANSLATION, entity_id=entity.id, language=target_language
        )
        self.jobs.mark_running(job)
        try:
            content = self.content.get_for_entity(entity.id, "en")
            if not content:
                raise ValueError(f"No English content for entity {entity.name}")

            fields = {}
            for field_name in [
                "description",
                "short_description",
                "iconography",
                "powers",
                "abilities",
                "boons",
                "curses",
                "teachings",
                "virtues",
                "flaws",
                "moral_lessons",
            ]:
                value = getattr(content, field_name, None)
                if value:
                    fields[field_name] = value

            lang_name = LANGUAGE_NAMES.get(target_language, target_language)
            user_prompt = TRANSLATION_PROMPT.format(
                target_language=lang_name,
                fields_json=json.dumps(fields, ensure_ascii=False, indent=2),
            )
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, TranslationSchema, purpose="translation"
            )
            for item in result.translations:
                self.languages.upsert(
                    entity_id=entity.id,
                    language=target_language,
                    field_name=item.field_name,
                    translated_text=item.translated_text,
                    source_language="en",
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.translations)}))
            logger.info(
                "Translated {} fields for {} to {}",
                len(result.translations),
                entity.name,
                target_language,
            )
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise

    def translate_all_fields_for_language(
        self, entities: list[Entity], target_language: str
    ) -> int:
        count = 0
        for entity in entities:
            try:
                self.translate_entity(entity, target_language)
                count += 1
            except Exception as exc:
                logger.error("Translation failed for {}: {}", entity.name, exc)
        return count
