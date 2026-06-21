from __future__ import annotations

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from purana_factory.database.base import Base, EntityStatus, EntityType, TimestampMixin


class Entity(Base, TimestampMixin):
    __tablename__ = "entity"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False, index=True)
    status: Mapped[EntityStatus] = mapped_column(
        Enum(EntityStatus), default=EntityStatus.PENDING, nullable=False, index=True
    )
    sanskrit_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    contents: Mapped[list["EntityContent"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    relationships_from: Mapped[list["EntityRelationship"]] = relationship(
        foreign_keys="EntityRelationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan",
    )
    relationships_to: Mapped[list["EntityRelationship"]] = relationship(
        foreign_keys="EntityRelationship.target_entity_id",
        back_populates="target_entity",
    )
    stories: Mapped[list["Story"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    temples: Mapped[list["Temple"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    festivals: Mapped[list["Festival"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    weapons: Mapped[list["Weapon"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    places: Mapped[list["Place"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    concepts: Mapped[list["Concept"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    image_assets: Mapped[list["ImageAsset"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    audio_assets: Mapped[list["AudioAsset"]] = relationship(back_populates="entity", cascade="all, delete-orphan")
    source_references: Mapped[list["SourceReference"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )
    language_contents: Mapped[list["LanguageContent"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )
    search_keywords: Mapped[list["SearchKeyword"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )
    generation_jobs: Mapped[list["GenerationJob"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )


from purana_factory.database.models.entity_content import EntityContent  # noqa: E402
from purana_factory.database.models.entity_relationship import EntityRelationship  # noqa: E402
from purana_factory.database.models.story import Story  # noqa: E402
from purana_factory.database.models.temple import Temple  # noqa: E402
from purana_factory.database.models.festival import Festival  # noqa: E402
from purana_factory.database.models.weapon import Weapon  # noqa: E402
from purana_factory.database.models.place import Place  # noqa: E402
from purana_factory.database.models.concept import Concept  # noqa: E402
from purana_factory.database.models.image_asset import ImageAsset  # noqa: E402
from purana_factory.database.models.audio_asset import AudioAsset  # noqa: E402
from purana_factory.database.models.source_reference import SourceReference  # noqa: E402
from purana_factory.database.models.language_content import LanguageContent  # noqa: E402
from purana_factory.database.models.search_keyword import SearchKeyword  # noqa: E402
from purana_factory.database.models.generation_job import GenerationJob  # noqa: E402
