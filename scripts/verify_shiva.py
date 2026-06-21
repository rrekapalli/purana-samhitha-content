"""Quick verification script for Shiva entity content."""

from purana_factory.config.settings import get_settings
from purana_factory.database.session import session_scope
from purana_factory.database.repositories import (
    ContentRepository,
    EntityRepository,
    FestivalRepository,
    KeywordRepository,
    PlaceRepository,
    RelationshipRepository,
    SourceRepository,
    StoryRepository,
    TempleRepository,
    WeaponRepository,
)

get_settings.cache_clear()

with session_scope() as session:
    entity = EntityRepository(session).get_by_name("Shiva")
    if not entity:
        print("Shiva not found")
        raise SystemExit(1)

    print(f"Entity: {entity.name} | type={entity.entity_type.value} | status={entity.status.value}")
    print(f"Sanskrit: {entity.sanskrit_name}")

    content = ContentRepository(session).get_for_entity(entity.id)
    if content:
        print(f"Description length: {len(content.description or '')} chars")
        print(f"Short: {(content.short_description or '')[:150]}...")

    print(f"Relationships: {len(RelationshipRepository(session).list_for_entity(entity.id))}")
    stories = StoryRepository(session).list_for_entity(entity.id)
    print(f"Stories: {len(stories)}")
    if stories:
        print(f"  First story: {stories[0].title}")
    print(f"Temples: {len(TempleRepository(session).list_for_entity(entity.id))}")
    print(f"Festivals: {len(FestivalRepository(session).list_for_entity(entity.id))}")
    print(f"Weapons: {len(WeaponRepository(session).list_for_entity(entity.id))}")
    print(f"Places: {len(PlaceRepository(session).list_for_entity(entity.id))}")
    print(f"Sources: {len(SourceRepository(session).list_for_entity(entity.id))}")
    print(f"Keywords: {len(KeywordRepository(session).list_for_entity(entity.id))}")
