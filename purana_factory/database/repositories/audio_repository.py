from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.models.audio_asset import AudioAsset


class AudioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        entity_id: int,
        duration_minutes: int,
        script: str,
        language: str = "en",
        provider: str | None = None,
    ) -> AudioAsset:
        asset = AudioAsset(
            entity_id=entity_id,
            duration_minutes=duration_minutes,
            script=script,
            language=language,
            provider=provider,
            status="PENDING",
        )
        self.session.add(asset)
        self.session.flush()
        return asset

    def list_pending(self, limit: int | None = None) -> list[AudioAsset]:
        stmt = select(AudioAsset).where(AudioAsset.status == "PENDING").order_by(AudioAsset.id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())

    def list_for_entity(self, entity_id: int) -> list[AudioAsset]:
        stmt = select(AudioAsset).where(AudioAsset.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())

    def update_status(self, asset: AudioAsset, status: str, file_path: str | None = None) -> AudioAsset:
        asset.status = status
        if file_path:
            asset.file_path = file_path
        self.session.flush()
        return asset
