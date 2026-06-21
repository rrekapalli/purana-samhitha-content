from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.base import RelationshipType
from purana_factory.database.models.entity_relationship import EntityRelationship


class RelationshipRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        source_entity_id: int,
        target_entity_id: int,
        relationship_type: RelationshipType,
        description: str | None = None,
        source_tradition: str | None = None,
        source_reference: str | None = None,
    ) -> EntityRelationship:
        rel = EntityRelationship(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            description=description,
            source_tradition=source_tradition,
            source_reference=source_reference,
        )
        self.session.add(rel)
        self.session.flush()
        return rel

    def list_for_entity(self, entity_id: int) -> list[EntityRelationship]:
        stmt = select(EntityRelationship).where(
            (EntityRelationship.source_entity_id == entity_id)
            | (EntityRelationship.target_entity_id == entity_id)
        )
        return list(self.session.scalars(stmt).all())

    def delete_for_entity(self, entity_id: int) -> None:
        for rel in self.list_for_entity(entity_id):
            self.session.delete(rel)
        self.session.flush()
