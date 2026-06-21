"""Clean generated content for an entity so it can be regenerated."""

from __future__ import annotations

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from purana_factory.database.base import EntityStatus
from purana_factory.database.models.audio_asset import AudioAsset
from purana_factory.database.models.concept import Concept
from purana_factory.database.models.entity import Entity
from purana_factory.database.models.entity_content import EntityContent
from purana_factory.database.models.entity_relationship import EntityRelationship
from purana_factory.database.models.festival import Festival
from purana_factory.database.models.generation_job import GenerationJob, GenerationLog
from purana_factory.database.models.image_asset import ImageAsset
from purana_factory.database.models.language_content import LanguageContent
from purana_factory.database.models.place import Place
from purana_factory.database.models.search_keyword import SearchKeyword
from purana_factory.database.models.source_reference import SourceReference
from purana_factory.database.models.story import Story, StoryVariant
from purana_factory.database.models.temple import Temple
from purana_factory.database.models.weapon import Weapon
from purana_factory.database.repositories import EntityRepository


def cleanup_entity_content(session: Session, entity_name: str) -> None:
    entity = EntityRepository(session).get_by_name(entity_name)
    if not entity:
        raise ValueError(f"Entity '{entity_name}' not found")

    entity_id = entity.id
    logger.info("Cleaning generated content for {} (id={})", entity_name, entity_id)

    # Story variants before stories
    story_ids = session.scalars(select(Story.id).where(Story.entity_id == entity_id)).all()
    if story_ids:
        session.execute(delete(StoryVariant).where(StoryVariant.story_id.in_(story_ids)))

    session.execute(delete(EntityContent).where(EntityContent.entity_id == entity_id))
    session.execute(
        delete(EntityRelationship).where(EntityRelationship.source_entity_id == entity_id)
    )
    session.execute(delete(Story).where(Story.entity_id == entity_id))
    session.execute(delete(Temple).where(Temple.entity_id == entity_id))
    session.execute(delete(Festival).where(Festival.entity_id == entity_id))
    session.execute(delete(Weapon).where(Weapon.entity_id == entity_id))
    session.execute(delete(Place).where(Place.entity_id == entity_id))
    session.execute(delete(Concept).where(Concept.entity_id == entity_id))
    session.execute(delete(ImageAsset).where(ImageAsset.entity_id == entity_id))
    session.execute(delete(AudioAsset).where(AudioAsset.entity_id == entity_id))
    session.execute(delete(SourceReference).where(SourceReference.entity_id == entity_id))
    session.execute(delete(LanguageContent).where(LanguageContent.entity_id == entity_id))
    session.execute(delete(SearchKeyword).where(SearchKeyword.entity_id == entity_id))

    job_ids = session.scalars(
        select(GenerationJob.id).where(GenerationJob.entity_id == entity_id)
    ).all()
    if job_ids:
        session.execute(delete(GenerationLog).where(GenerationLog.job_id.in_(job_ids)))
    session.execute(delete(GenerationJob).where(GenerationJob.entity_id == entity_id))

    entity.status = EntityStatus.PENDING
    entity.sanskrit_name = None
    session.flush()
    logger.info("Cleanup complete for {}", entity_name)
