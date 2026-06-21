"""Pipeline orchestration and job engine."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.config import get_settings
from purana_factory.database.base import EntityStatus, EntityType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import EntityRepository
from purana_factory.services.audio.service import AudioGenerationService, NarrationService
from purana_factory.services.bootstrap.service import BootstrapService
from purana_factory.services.content.ancillary import (
    FestivalService,
    PlaceService,
    TempleService,
    WeaponService,
)
from purana_factory.services.content.entity_profile import EntityProfileService
from purana_factory.services.content.relationships import RelationshipService
from purana_factory.services.content.stories import StoryService
from purana_factory.services.export.service import ExportService
from purana_factory.services.image.service import ImageGenerationService, ImagePromptService
from purana_factory.services.ollama import OllamaService
from purana_factory.services.translation.service import TranslationService
from purana_factory.services.validation.service import ValidationService


class PipelineType(str, Enum):
    ALL = "all"
    CONTENT = "content"
    IMAGES = "images"
    NARRATION = "narration"
    TRANSLATION = "translation"
    VALIDATION = "validation"
    EXPORT = "export"
    BOOTSTRAP = "bootstrap"


@dataclass
class StepTiming:
    step: str
    duration_seconds: float


@dataclass
class PipelineTiming:
    entity_name: str
    total_seconds: float = 0.0
    steps: list[StepTiming] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entity_name": self.entity_name,
            "total_seconds": round(self.total_seconds, 2),
            "total_minutes": round(self.total_seconds / 60, 2),
            "steps": [
                {"step": s.step, "duration_seconds": round(s.duration_seconds, 2)}
                for s in self.steps
            ],
        }


class ContentPipeline:
    """Runs the 7-step content generation pipeline for entities."""

    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.profile = EntityProfileService(session, self.ollama)
        self.relationships = RelationshipService(session, self.ollama)
        self.stories = StoryService(session, self.ollama)
        self.temples = TempleService(session, self.ollama)
        self.festivals = FestivalService(session, self.ollama)
        self.weapons = WeaponService(session, self.ollama)
        self.places = PlaceService(session, self.ollama)

    def run_for_entity(self, entity: Entity, language: str = "en") -> PipelineTiming:
        timing = PipelineTiming(entity_name=entity.name)
        pipeline_start = time.perf_counter()
        logger.info("Starting content pipeline for: {}", entity.name)

        steps: list[tuple[str, Callable[[], None]]] = [
            ("entity_profile", lambda: self.profile.generate(entity, language=language)),
            ("relationships", lambda: self.relationships.generate(entity)),
            ("stories", lambda: self.stories.generate(entity, language=language)),
            ("temples", lambda: self.temples.generate(entity, language=language)),
            ("festivals", lambda: self.festivals.generate(entity, language=language)),
            ("weapons", lambda: self.weapons.generate(entity, language=language)),
            ("places", lambda: self.places.generate(entity, language=language)),
        ]

        for step_name, step_fn in steps:
            step_start = time.perf_counter()
            step_fn()
            step_duration = time.perf_counter() - step_start
            timing.steps.append(StepTiming(step=step_name, duration_seconds=step_duration))
            logger.info(
                "Step '{}' completed in {:.1f}s for {}",
                step_name,
                step_duration,
                entity.name,
            )

        EntityRepository(self.session).update_status(entity, EntityStatus.COMPLETED)
        timing.total_seconds = time.perf_counter() - pipeline_start
        logger.info(
            "Completed content pipeline for {} in {:.1f}s ({:.1f} min)",
            entity.name,
            timing.total_seconds,
            timing.total_seconds / 60,
        )
        return timing


class JobEngine:
    """Resumable batch job execution engine."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.entities = EntityRepository(session)
        self.ollama = OllamaService()
        self.content_pipeline = ContentPipeline(session, self.ollama)
        self.image_prompts = ImagePromptService(session, self.ollama)
        self.image_gen = ImageGenerationService(session)
        self.narration = NarrationService(session, self.ollama)
        self.audio_gen = AudioGenerationService(session)
        self.translation = TranslationService(session, self.ollama)
        self.validation = ValidationService(session)
        self.export = ExportService(session)
        self.bootstrap = BootstrapService(session)

    def _resolve_entities(
        self,
        entity_type: EntityType | None = None,
        entity_name: str | None = None,
        all_pending: bool = False,
        limit: int | None = None,
    ) -> list[Entity]:
        if entity_name:
            entity = self.entities.get_by_name(entity_name)
            return [entity] if entity else []
        if all_pending:
            return self.entities.list_pending(entity_type=entity_type, limit=limit)
        if entity_type:
            return self.entities.list_pending(entity_type=entity_type, limit=limit)
        return []

    def run(
        self,
        pipeline: PipelineType,
        entity_type: EntityType | None = None,
        entity_name: str | None = None,
        all_pending: bool = False,
        language: str = "en",
        limit: int | None = None,
    ) -> dict:
        if limit is None and all_pending:
            limit = self.settings.generation.batch_size

        results: dict = {"pipeline": pipeline.value, "processed": 0, "errors": []}

        if pipeline == PipelineType.BOOTSTRAP:
            created, skipped = self.bootstrap.load_entities()
            results["created"] = created
            results["skipped"] = skipped
            return results

        entities = self._resolve_entities(entity_type, entity_name, all_pending, limit)

        if pipeline == PipelineType.CONTENT or pipeline == PipelineType.ALL:
            if not entities and not entity_name:
                entities = self.entities.list_pending(limit=limit)
            timings: list[dict] = []
            for entity in entities:
                try:
                    timing = self.content_pipeline.run_for_entity(entity, language=language)
                    timings.append(timing.to_dict())
                    results["processed"] += 1
                except Exception as exc:
                    logger.error("Content pipeline failed for {}: {}", entity.name, exc)
                    results["errors"].append({"entity": entity.name, "error": str(exc)})
            if timings:
                results["timings"] = timings

        if pipeline == PipelineType.IMAGES or pipeline == PipelineType.ALL:
            if not entities:
                entities = self.entities.list_all()
            for entity in entities:
                try:
                    self.image_prompts.generate_prompts(entity)
                except Exception as exc:
                    results["errors"].append({"entity": entity.name, "error": str(exc)})
            generated = self.image_gen.generate_pending(limit=limit)
            results["images_generated"] = generated

        if pipeline == PipelineType.NARRATION or pipeline == PipelineType.ALL:
            if not entities:
                entities = self.entities.list_all()
            for entity in entities:
                try:
                    self.narration.generate_scripts(entity, language=language)
                    results["processed"] += 1
                except Exception as exc:
                    results["errors"].append({"entity": entity.name, "error": str(exc)})
            audio_count = self.audio_gen.generate_pending(limit=limit)
            results["audio_generated"] = audio_count

        if pipeline == PipelineType.TRANSLATION or pipeline == PipelineType.ALL:
            if not entities:
                entities = self.entities.list_all()
            if language != "en":
                count = self.translation.translate_all_fields_for_language(entities, language)
                results["translated"] = count

        if pipeline == PipelineType.VALIDATION or pipeline == PipelineType.ALL:
            report = self.validation.validate_all()
            results["validation"] = report.to_dict()

        if pipeline == PipelineType.EXPORT or pipeline == PipelineType.ALL:
            exports = self.export.export_all()
            results["exports"] = {k: str(v) for k, v in exports.items()}

        return results
