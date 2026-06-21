from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.temple import Temple


class TempleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity_id: int, data: dict, language: str = "en") -> Temple:
        temple = Temple(entity_id=entity_id, language=language, **data)
        self.session.add(temple)
        self.session.flush()
        return temple

    def list_for_entity(self, entity_id: int) -> list[Temple]:
        stmt = select(Temple).where(Temple.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())
