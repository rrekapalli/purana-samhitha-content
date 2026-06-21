from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.base import EntityStatus, EntityType
from purana_factory.database.models.entity import Entity


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "entity"


class EntityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, entity_type: EntityType, sanskrit_name: str | None = None) -> Entity:
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while self.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        entity = Entity(
            name=name,
            entity_type=entity_type,
            status=EntityStatus.PENDING,
            sanskrit_name=sanskrit_name,
            slug=slug,
        )
        self.session.add(entity)
        self.session.flush()
        return entity

    def get_by_id(self, entity_id: int) -> Entity | None:
        return self.session.get(Entity, entity_id)

    def get_by_name(self, name: str) -> Entity | None:
        stmt = select(Entity).where(Entity.name == name)
        return self.session.scalars(stmt).first()

    def get_by_slug(self, slug: str) -> Entity | None:
        stmt = select(Entity).where(Entity.slug == slug)
        return self.session.scalars(stmt).first()

    def list_pending(self, entity_type: EntityType | None = None, limit: int | None = None) -> list[Entity]:
        stmt = select(Entity).where(Entity.status == EntityStatus.PENDING)
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        stmt = stmt.order_by(Entity.id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())

    def list_all(self, entity_type: EntityType | None = None) -> list[Entity]:
        stmt = select(Entity).order_by(Entity.name)
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        return list(self.session.scalars(stmt).all())

    def update_status(self, entity: Entity, status: EntityStatus) -> Entity:
        entity.status = status
        self.session.flush()
        return entity

    def count_by_status(self, status: EntityStatus) -> int:
        stmt = select(Entity).where(Entity.status == status)
        return len(list(self.session.scalars(stmt).all()))
