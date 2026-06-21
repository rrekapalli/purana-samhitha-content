from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, TimestampMixin


class EntityContent(Base, TimestampMixin):
    __tablename__ = "entity_content"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True)
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    iconography: Mapped[str | None] = mapped_column(Text, nullable=True)
    powers: Mapped[str | None] = mapped_column(Text, nullable=True)
    abilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    boons: Mapped[str | None] = mapped_column(Text, nullable=True)
    curses: Mapped[str | None] = mapped_column(Text, nullable=True)
    teachings: Mapped[str | None] = mapped_column(Text, nullable=True)
    virtues: Mapped[str | None] = mapped_column(Text, nullable=True)
    flaws: Mapped[str | None] = mapped_column(Text, nullable=True)
    moral_lessons: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="contents")


from purana_factory.database.models.entity import Entity  # noqa: E402
