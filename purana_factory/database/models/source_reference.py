from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, TimestampMixin


class SourceReference(Base, TimestampMixin):
    __tablename__ = "source_reference"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True)
    scripture: Mapped[str] = mapped_column(String(255), nullable=False)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    tradition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    entity: Mapped["Entity"] = relationship(back_populates="source_references")


from purana_factory.database.models.entity import Entity  # noqa: E402
