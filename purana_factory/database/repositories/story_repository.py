from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.story import Story, StoryVariant


class StoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity_id: int, data: dict, language: str = "en") -> Story:
        story = Story(entity_id=entity_id, language=language, **data)
        self.session.add(story)
        self.session.flush()
        return story

    def add_variant(self, story_id: int, data: dict) -> StoryVariant:
        variant = StoryVariant(story_id=story_id, **data)
        self.session.add(variant)
        self.session.flush()
        return variant

    def list_for_entity(self, entity_id: int) -> list[Story]:
        stmt = select(Story).where(Story.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())

    def delete_for_entity(self, entity_id: int) -> None:
        for story in self.list_for_entity(entity_id):
            self.session.delete(story)
        self.session.flush()
