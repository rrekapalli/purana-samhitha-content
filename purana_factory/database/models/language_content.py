from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, TimestampMixin


class LanguageContent(Base, TimestampMixin):
    __tablename__ = "language_content"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="language_contents")


from purana_factory.database.models.entity import Entity  # noqa: E402
