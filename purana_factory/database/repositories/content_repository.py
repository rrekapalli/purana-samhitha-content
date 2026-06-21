from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.entity_content import EntityContent


class ContentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity_id: int, data: dict, language: str = "en") -> EntityContent:
        content = EntityContent(entity_id=entity_id, language=language, **data)
        self.session.add(content)
        self.session.flush()
        return content

    def get_for_entity(self, entity_id: int, language: str = "en") -> EntityContent | None:
        stmt = select(EntityContent).where(
            EntityContent.entity_id == entity_id,
            EntityContent.language == language,
        )
        return self.session.scalars(stmt).first()

    def upsert(self, entity_id: int, data: dict, language: str = "en") -> EntityContent:
        existing = self.get_for_entity(entity_id, language)
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            self.session.flush()
            return existing
        return self.create(entity_id, data, language)
