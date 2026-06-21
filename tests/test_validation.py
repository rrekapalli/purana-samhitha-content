"""Validation service tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from purana_factory.database.base import Base, EntityType
from purana_factory.database.repositories.content_repository import ContentRepository
from purana_factory.database.repositories.entity_repository import EntityRepository
from purana_factory.services.validation.service import ValidationService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


def test_validate_missing_content(session):
    repo = EntityRepository(session)
    entity = repo.create("Test", EntityType.DEITY)
    service = ValidationService(session)
    issues = service.validate_entity(entity)
    assert any(i.issue_type == "MISSING_CONTENT" for i in issues)


def test_validate_complete_entity(session):
    entity_repo = EntityRepository(session)
    content_repo = ContentRepository(session)
    entity = entity_repo.create("Shiva", EntityType.DEITY)
    content_repo.create(
        entity.id,
        {
            "description": "A" * 200,
            "short_description": "God of destruction",
        },
    )
    from purana_factory.database.repositories.source_repository import SourceRepository

    SourceRepository(session).create(entity.id, "Shiva Purana", citation="Chapter 1")
    service = ValidationService(session)
    issues = service.validate_entity(entity)
    assert len(issues) == 0
