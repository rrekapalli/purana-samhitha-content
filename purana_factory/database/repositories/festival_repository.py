from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.festival import Festival


class FestivalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity_id: int, data: dict, language: str = "en") -> Festival:
        festival = Festival(entity_id=entity_id, language=language, **data)
        self.session.add(festival)
        self.session.flush()
        return festival

    def list_for_entity(self, entity_id: int) -> list[Festival]:
        stmt = select(Festival).where(Festival.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())
