from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.search_keyword import SearchKeyword


class KeywordRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_keywords(self, entity_id: int, keywords: list[str], language: str = "en") -> list[SearchKeyword]:
        results = []
        for keyword in keywords:
            kw = keyword.strip()
            if not kw:
                continue
            existing = self.session.scalars(
                select(SearchKeyword).where(
                    SearchKeyword.entity_id == entity_id,
                    SearchKeyword.keyword == kw,
                    SearchKeyword.language == language,
                )
            ).first()
            if existing:
                results.append(existing)
                continue
            record = SearchKeyword(entity_id=entity_id, keyword=kw, language=language)
            self.session.add(record)
            results.append(record)
        self.session.flush()
        return results

    def list_for_entity(self, entity_id: int) -> list[SearchKeyword]:
        stmt = select(SearchKeyword).where(SearchKeyword.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())

    def delete_for_entity(self, entity_id: int) -> None:
        for kw in self.list_for_entity(entity_id):
            self.session.delete(kw)
        self.session.flush()
