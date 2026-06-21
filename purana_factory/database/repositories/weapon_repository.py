from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.weapon import Weapon


class WeaponRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, entity_id: int, data: dict, language: str = "en") -> Weapon:
        weapon = Weapon(entity_id=entity_id, language=language, **data)
        self.session.add(weapon)
        self.session.flush()
        return weapon

    def list_for_entity(self, entity_id: int) -> list[Weapon]:
        stmt = select(Weapon).where(Weapon.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())
