from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, RelationshipType, TimestampMixin


class EntityRelationship(Base, TimestampMixin):
    __tablename__ = "entity_relationship"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(Enum(RelationshipType), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_tradition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_entity: Mapped["Entity"] = relationship(
        foreign_keys=[source_entity_id], back_populates="relationships_from"
    )
    target_entity: Mapped["Entity"] = relationship(
        foreign_keys=[target_entity_id], back_populates="relationships_to"
    )


from purana_factory.database.models.entity import Entity  # noqa: E402
