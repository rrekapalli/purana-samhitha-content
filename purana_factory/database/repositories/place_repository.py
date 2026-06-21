from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.place import Place


class PlaceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity_id: int, data: dict, language: str = "en") -> Place:
        place = Place(entity_id=entity_id, language=language, **data)
        self.session.add(place)
        self.session.flush()
        return place

    def list_for_entity(self, entity_id: int) -> list[Place]:
        stmt = select(Place).where(Place.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())
