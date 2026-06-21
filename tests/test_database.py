"""Database and model tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from purana_factory.database.base import Base, EntityStatus, EntityType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories.entity_repository import EntityRepository, slugify


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


def test_slugify():
    assert slugify("Shiva") == "shiva"
    assert slugify("Lord Vishnu") == "lord-vishnu"


def test_create_entity(session):
    repo = EntityRepository(session)
    entity = repo.create("Shiva", EntityType.DEITY, sanskrit_name="शिव")
    assert entity.name == "Shiva"
    assert entity.entity_type == EntityType.DEITY
    assert entity.status == EntityStatus.PENDING
    assert entity.slug == "shiva"


def test_get_by_name(session):
    repo = EntityRepository(session)
    repo.create("Krishna", EntityType.AVATAR)
    found = repo.get_by_name("Krishna")
    assert found is not None
    assert found.name == "Krishna"


def test_list_pending(session):
    repo = EntityRepository(session)
    repo.create("Rama", EntityType.AVATAR)
    repo.create("Sita", EntityType.CHARACTER)
    pending = repo.list_pending()
    assert len(pending) == 2


def test_duplicate_slug_handling(session):
    repo = EntityRepository(session)
    repo.create("Shiva", EntityType.DEITY)
    second = repo.create("Shiva", EntityType.DEITY)
    assert second.slug == "shiva-1"
