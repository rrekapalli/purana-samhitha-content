"""SQLAlchemy declarative base and enums."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class EntityType(str, enum.Enum):
    DEITY = "DEITY"
    CHARACTER = "CHARACTER"
    SAGE = "SAGE"
    RISHI = "RISHI"
    DEMON = "DEMON"
    ASURA = "ASURA"
    KING = "KING"
    QUEEN = "QUEEN"
    DYNASTY = "DYNASTY"
    KINGDOM = "KINGDOM"
    TEMPLE = "TEMPLE"
    PLACE = "PLACE"
    MOUNTAIN = "MOUNTAIN"
    RIVER = "RIVER"
    WEAPON = "WEAPON"
    OBJECT = "OBJECT"
    ANIMAL = "ANIMAL"
    VEHICLE = "VEHICLE"
    SCRIPTURE = "SCRIPTURE"
    FESTIVAL = "FESTIVAL"
    EVENT = "EVENT"
    CONCEPT = "CONCEPT"
    AVATAR = "AVATAR"


class EntityStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RelationshipType(str, enum.Enum):
    FATHER_OF = "FATHER_OF"
    MOTHER_OF = "MOTHER_OF"
    CHILD_OF = "CHILD_OF"
    CONSORT_OF = "CONSORT_OF"
    DISCIPLE_OF = "DISCIPLE_OF"
    GURU_OF = "GURU_OF"
    ALLY_OF = "ALLY_OF"
    ENEMY_OF = "ENEMY_OF"
    AVATAR_OF = "AVATAR_OF"
    INCARNATION_OF = "INCARNATION_OF"
    USES = "USES"
    RIDES = "RIDES"
    OWNS = "OWNS"
    RULES = "RULES"
    RESIDES_AT = "RESIDES_AT"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    WORSHIPPED_AT = "WORSHIPPED_AT"


class ImageType(str, enum.Enum):
    PORTRAIT = "PORTRAIT"
    TEMPLE = "TEMPLE"
    STORY = "STORY"
    WEAPON = "WEAPON"
    FESTIVAL = "FESTIVAL"
    FAMILY_TREE = "FAMILY_TREE"
    KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"


class JobType(str, enum.Enum):
    ENTITY_PROFILE = "ENTITY_PROFILE"
    RELATIONSHIPS = "RELATIONSHIPS"
    STORIES = "STORIES"
    TEMPLES = "TEMPLES"
    FESTIVALS = "FESTIVALS"
    WEAPONS = "WEAPONS"
    PLACES = "PLACES"
    IMAGE_PROMPT = "IMAGE_PROMPT"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    NARRATION_SCRIPT = "NARRATION_SCRIPT"
    AUDIO_GENERATION = "AUDIO_GENERATION"
    TRANSLATION = "TRANSLATION"
    VALIDATION = "VALIDATION"
    EXPORT = "EXPORT"
    BOOTSTRAP = "BOOTSTRAP"
