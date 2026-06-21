"""Bootstrap service tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from purana_factory.database.base import Base
from purana_factory.database.repositories.entity_repository import EntityRepository
from purana_factory.services.bootstrap.entities import BOOTSTRAP_ENTITIES
from purana_factory.services.bootstrap.service import BootstrapService


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()


def test_bootstrap_entities_count():
    assert len(BOOTSTRAP_ENTITIES) >= 100


def test_bootstrap_load(session):
    service = BootstrapService(session)
    created, skipped = service.load_entities()
    assert created == len(BOOTSTRAP_ENTITIES)
    assert skipped == 0

    repo = EntityRepository(session)
    assert repo.get_by_name("Shiva") is not None
    assert repo.get_by_name("Krishna") is not None


def test_bootstrap_idempotent(session):
    service = BootstrapService(session)
    service.load_entities()
    created, skipped = service.load_entities()
    assert created == 0
    assert skipped == len(BOOTSTRAP_ENTITIES)
