from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.source_reference import SourceReference


class SourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        entity_id: int,
        scripture: str,
        citation: str | None = None,
        tradition: str | None = None,
        notes: str | None = None,
    ) -> SourceReference:
        ref = SourceReference(
            entity_id=entity_id,
            scripture=scripture,
            citation=citation,
            tradition=tradition,
            notes=notes,
        )
        self.session.add(ref)
        self.session.flush()
        return ref

    def list_for_entity(self, entity_id: int) -> list[SourceReference]:
        stmt = select(SourceReference).where(SourceReference.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())

    def delete_for_entity(self, entity_id: int) -> None:
        for ref in self.list_for_entity(entity_id):
            self.session.delete(ref)
        self.session.flush()
