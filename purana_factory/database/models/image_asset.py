from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, ImageType, TimestampMixin


class ImageAsset(Base, TimestampMixin):
    __tablename__ = "image_asset"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True)
    image_type: Mapped[ImageType] = mapped_column(Enum(ImageType), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="image_assets")


from purana_factory.database.models.entity import Entity  # noqa: E402
