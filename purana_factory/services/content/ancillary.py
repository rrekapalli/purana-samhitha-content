"""Temple, festival, weapon, and place generation services."""

from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.database.base import JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import (
    FestivalRepository,
    JobRepository,
    PlaceRepository,
    TempleRepository,
    WeaponRepository,
)
from purana_factory.services.content.prompts import (
    FESTIVALS_PROMPT,
    PLACES_PROMPT,
    SYSTEM_PROMPT,
    TEMPLES_PROMPT,
    WEAPONS_PROMPT,
)
from purana_factory.services.content.schemas import FestivalsSchema, PlacesSchema, TemplesSchema, WeaponsSchema
from purana_factory.services.ollama import OllamaService


def _list_to_text(items: list[str] | None) -> str | None:
    if not items:
        return None
    return "\n".join(f"- {item}" for item in items)


class TempleService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.temples = TempleRepository(session)
        self.jobs = JobRepository(session)

    def generate(self, entity: Entity, language: str = "en") -> TemplesSchema:
        job = self.jobs.create(JobType.TEMPLES, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            user_prompt = TEMPLES_PROMPT.format(name=entity.name)
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, TemplesSchema, purpose="content"
            )
            for t in result.temples:
                self.temples.create(
                    entity.id,
                    {
                        "name": t.name,
                        "location": t.location,
                        "description": t.description,
                        "significance": t.significance,
                        "pilgrimage_info": t.pilgrimage_info,
                        "associated_deities": _list_to_text(t.associated_deities),
                    },
                    language=language,
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.temples)}))
            logger.info("Generated {} temples for {}", len(result.temples), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise


class FestivalService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.festivals = FestivalRepository(session)
        self.jobs = JobRepository(session)

    def generate(self, entity: Entity, language: str = "en") -> FestivalsSchema:
        job = self.jobs.create(JobType.FESTIVALS, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            user_prompt = FESTIVALS_PROMPT.format(name=entity.name)
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, FestivalsSchema, purpose="content"
            )
            for f in result.festivals:
                self.festivals.create(
                    entity.id,
                    {
                        "name": f.name,
                        "description": f.description,
                        "rituals": _list_to_text(f.rituals),
                        "associated_deities": _list_to_text(f.associated_deities),
                        "calendar_info": f.calendar_info,
                    },
                    language=language,
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.festivals)}))
            logger.info("Generated {} festivals for {}", len(result.festivals), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise


class WeaponService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.weapons = WeaponRepository(session)
        self.jobs = JobRepository(session)

    def generate(self, entity: Entity, language: str = "en") -> WeaponsSchema:
        job = self.jobs.create(JobType.WEAPONS, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            user_prompt = WEAPONS_PROMPT.format(name=entity.name)
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, WeaponsSchema, purpose="content"
            )
            for w in result.weapons:
                self.weapons.create(
                    entity.id,
                    {
                        "name": w.name,
                        "history": w.history,
                        "powers": _list_to_text(w.powers),
                        "owners": _list_to_text(w.owners),
                        "associated_stories": _list_to_text(w.associated_stories),
                    },
                    language=language,
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.weapons)}))
            logger.info("Generated {} weapons for {}", len(result.weapons), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise


class PlaceService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.places = PlaceRepository(session)
        self.jobs = JobRepository(session)

    def generate(self, entity: Entity, language: str = "en") -> PlacesSchema:
        job = self.jobs.create(JobType.PLACES, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            user_prompt = PLACES_PROMPT.format(name=entity.name)
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, PlacesSchema, purpose="content"
            )
            for p in result.places:
                self.places.create(
                    entity.id,
                    {
                        "name": p.name,
                        "place_type": p.place_type,
                        "description": p.description,
                        "significance": p.significance,
                        "geography": p.geography,
                    },
                    language=language,
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.places)}))
            logger.info("Generated {} places for {}", len(result.places), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise
