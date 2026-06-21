"""Export service for JSON, CSV, and SQL."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from purana_factory.config import get_settings
from purana_factory.database.base import JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.models.entity_content import EntityContent
from purana_factory.database.models.entity_relationship import EntityRelationship
from purana_factory.database.models.story import Story
from purana_factory.database.repositories import JobRepository


class ExportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.jobs = JobRepository(session)
        self.settings = get_settings()

    def _output_dir(self) -> Path:
        path = self.settings.resolve_path(self.settings.export.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def export_json(self) -> Path:
        job = self.jobs.create(JobType.EXPORT, payload="json")
        self.jobs.mark_running(job)
        try:
            entities = self.session.scalars(select(Entity)).all()
            data = []
            for entity in entities:
                content = self.session.scalars(
                    select(EntityContent).where(EntityContent.entity_id == entity.id)
                ).first()
                data.append(
                    {
                        "id": entity.id,
                        "name": entity.name,
                        "entity_type": entity.entity_type.value,
                        "status": entity.status.value,
                        "sanskrit_name": entity.sanskrit_name,
                        "slug": entity.slug,
                        "content": {
                            "description": content.description if content else None,
                            "short_description": content.short_description if content else None,
                        },
                    }
                )
            output = self._output_dir() / f"entities_{self._timestamp()}.json"
            with output.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.jobs.mark_completed(job, result=str(output))
            logger.info("Exported JSON to {}", output)
            return output
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc))
            raise

    def export_csv(self) -> Path:
        job = self.jobs.create(JobType.EXPORT, payload="csv")
        self.jobs.mark_running(job)
        try:
            entities = self.session.scalars(select(Entity)).all()
            output = self._output_dir() / f"entities_{self._timestamp()}.csv"
            with output.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "name", "entity_type", "status", "sanskrit_name", "slug"])
                for entity in entities:
                    writer.writerow(
                        [
                            entity.id,
                            entity.name,
                            entity.entity_type.value,
                            entity.status.value,
                            entity.sanskrit_name or "",
                            entity.slug,
                        ]
                    )
            self.jobs.mark_completed(job, result=str(output))
            logger.info("Exported CSV to {}", output)
            return output
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc))
            raise

    def export_sql(self) -> Path:
        job = self.jobs.create(JobType.EXPORT, payload="sql")
        self.jobs.mark_running(job)
        try:
            db_path = self.settings.resolve_path(self.settings.database.path)
            output = self._output_dir() / f"dump_{self._timestamp()}.sql"
            conn = sqlite3.connect(str(db_path))
            with output.open("w", encoding="utf-8") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()
            self.jobs.mark_completed(job, result=str(output))
            logger.info("Exported SQL to {}", output)
            return output
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc))
            raise

    def export_all(self) -> dict[str, Path]:
        return {
            "json": self.export_json(),
            "csv": self.export_csv(),
            "sql": self.export_sql(),
        }
