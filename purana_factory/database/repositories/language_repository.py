from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.language_content import LanguageContent


class LanguageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        entity_id: int,
        language: str,
        field_name: str,
        translated_text: str,
        source_language: str = "en",
    ) -> LanguageContent:
        stmt = select(LanguageContent).where(
            LanguageContent.entity_id == entity_id,
            LanguageContent.language == language,
            LanguageContent.field_name == field_name,
        )
        existing = self.session.scalars(stmt).first()
        if existing:
            existing.translated_text = translated_text
            self.session.flush()
            return existing
        content = LanguageContent(
            entity_id=entity_id,
            language=language,
            field_name=field_name,
            translated_text=translated_text,
            source_language=source_language,
        )
        self.session.add(content)
        self.session.flush()
        return content

    def list_for_entity(self, entity_id: int, language: str | None = None) -> list[LanguageContent]:
        stmt = select(LanguageContent).where(LanguageContent.entity_id == entity_id)
        if language:
            stmt = stmt.where(LanguageContent.language == language)
        return list(self.session.scalars(stmt).all())
