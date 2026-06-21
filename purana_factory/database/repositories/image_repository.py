from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.database.base import ImageType
from purana_factory.database.models.image_asset import ImageAsset


class ImageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        entity_id: int,
        image_type: ImageType,
        prompt: str,
        style: str | None = None,
        provider: str | None = None,
    ) -> ImageAsset:
        asset = ImageAsset(
            entity_id=entity_id,
            image_type=image_type,
            prompt=prompt,
            style=style,
            provider=provider,
            status="PENDING",
        )
        self.session.add(asset)
        self.session.flush()
        return asset

    def list_pending(self, limit: int | None = None) -> list[ImageAsset]:
        stmt = select(ImageAsset).where(ImageAsset.status == "PENDING").order_by(ImageAsset.id)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())

    def list_for_entity(self, entity_id: int) -> list[ImageAsset]:
        stmt = select(ImageAsset).where(ImageAsset.entity_id == entity_id)
        return list(self.session.scalars(stmt).all())

    def update_status(self, asset: ImageAsset, status: str, file_path: str | None = None) -> ImageAsset:
        asset.status = status
        if file_path:
            asset.file_path = file_path
        self.session.flush()
        return asset
