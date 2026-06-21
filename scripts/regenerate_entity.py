"""Clean, regenerate, and export entity content with timing metrics."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from purana_factory.config.settings import get_settings
from purana_factory.database.repositories import EntityRepository
from purana_factory.database.session import session_scope
from purana_factory.jobs.engine import ContentPipeline
from purana_factory.logging_setup import setup_logging
from purana_factory.services.cleanup import cleanup_entity_content
from purana_factory.services.ollama import OllamaService

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_entity_folder import export_entity  # noqa: E402


def regenerate_entity(entity_name: str, output_folder: Path | None = None) -> dict:
    setup_logging()
    get_settings.cache_clear()
    root = Path(__file__).resolve().parent.parent
    out = output_folder or (root / entity_name.lower())

    total_start = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    timing = None

    with session_scope() as session:
        cleanup_entity_content(session, entity_name)
        entity = EntityRepository(session).get_by_name(entity_name)
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")
        pipeline = ContentPipeline(session, OllamaService())
        timing = pipeline.run_for_entity(entity)

    total_seconds = time.perf_counter() - total_start
    metrics = {
        "entity_name": entity_name,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "total_seconds": round(total_seconds, 2),
        "total_minutes": round(total_seconds / 60, 2),
        "pipeline_steps": timing.to_dict() if timing else {},
    }

    files = export_entity(entity_name, out, timing_metrics=metrics, clear_existing=True)

    metrics["exported_files"] = len(files)
    (out / "generation_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(metrics, indent=2))
    print(f"\nExported {len(files)} files to {out}")
    return metrics


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Shiva"
    regenerate_entity(name)
