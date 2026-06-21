from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, TimestampMixin


class Festival(Base, TimestampMixin):
    __tablename__ = "festival"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rituals: Mapped[str | None] = mapped_column(Text, nullable=True)
    associated_deities: Mapped[str | None] = mapped_column(Text, nullable=True)
    calendar_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="festivals")


from purana_factory.database.models.entity import Entity  # noqa: E402
