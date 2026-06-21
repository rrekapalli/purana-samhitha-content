"""Typer CLI application."""

from __future__ import annotations

from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from purana_factory.config import get_settings
from purana_factory.database.base import EntityType
from purana_factory.database.session import init_database, session_scope
from purana_factory.jobs.engine import JobEngine, PipelineType
from purana_factory.logging_setup import setup_logging
from purana_factory.services.ollama import OllamaService

app = typer.Typer(
    name="purana-factory",
    help="Purana Samhitha Content Factory - Hindu mythology content generation",
    no_args_is_help=True,
)
console = Console()


class PipelineChoice(str, Enum):
    all = "all"
    content = "content"
    images = "images"
    narration = "narration"
    translation = "translation"
    validation = "validation"
    export = "export"
    bootstrap = "bootstrap"


class EntityTypeChoice(str, Enum):
    DEITY = "DEITY"
    CHARACTER = "CHARACTER"
    SAGE = "SAGE"
    RISHI = "RISHI"
    DEMON = "DEMON"
    ASURA = "ASURA"
    KING = "KING"
    QUEEN = "QUEEN"
    DYNASTY = "DYNASTY"
    KINGDOM = "KINGDOM"
    TEMPLE = "TEMPLE"
    PLACE = "PLACE"
    MOUNTAIN = "MOUNTAIN"
    RIVER = "RIVER"
    WEAPON = "WEAPON"
    OBJECT = "OBJECT"
    ANIMAL = "ANIMAL"
    VEHICLE = "VEHICLE"
    SCRIPTURE = "SCRIPTURE"
    FESTIVAL = "FESTIVAL"
    EVENT = "EVENT"
    CONCEPT = "CONCEPT"
    AVATAR = "AVATAR"


def _ensure_dirs() -> None:
    settings = get_settings()
    for path_key in [
        settings.paths.generated_images,
        settings.paths.generated_audio,
        settings.paths.generated_json,
        settings.export.output_dir,
        settings.paths.logs,
    ]:
        settings.resolve_path(path_key).mkdir(parents=True, exist_ok=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    pipeline: Optional[PipelineChoice] = typer.Option(
        None, "--pipeline", help="Pipeline to run"
    ),
    entity_type: Optional[EntityTypeChoice] = typer.Option(
        None, "--entity-type", help="Filter by entity type"
    ),
    entity_name: Optional[str] = typer.Option(
        None, "--entity-name", help="Process specific entity by name"
    ),
    all_entities: bool = typer.Option(
        False, "--all", help="Process all pending entities"
    ),
    language: str = typer.Option("en", "--language", help="Target language code"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Max entities to process"),
    init_db: bool = typer.Option(True, "--init-db/--no-init-db", help="Initialize database"),
) -> None:
    """Run content generation pipelines."""
    if ctx.invoked_subcommand is not None:
        return

    setup_logging()
    _ensure_dirs()

    if init_db:
        init_database()
        console.print("[green]Database initialized[/green]")

    if pipeline is None and not all_entities and entity_name is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    selected_pipeline = PipelineType(pipeline.value if pipeline else "content")
    etype = EntityType(entity_type.value) if entity_type else None

    with session_scope() as session:
        engine = JobEngine(session)
        results = engine.run(
            pipeline=selected_pipeline,
            entity_type=etype,
            entity_name=entity_name,
            all_pending=all_entities,
            language=language,
            limit=limit,
        )

    table = Table(title="Pipeline Results")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    for key, value in results.items():
        table.add_row(str(key), str(value))
    console.print(table)


@app.command("status")
def status() -> None:
    """Show system status and entity counts."""
    setup_logging()
    init_database()
    settings = get_settings()
    ollama = OllamaService()

    console.print(f"[bold]Ollama Host:[/bold] {settings.ollama.base_url}")
    console.print(f"[bold]Default Model:[/bold] {settings.ollama.default_model}")

    if ollama.health_check():
        console.print("[green]Ollama: Connected[/green]")
        models = ollama.list_models()
        if models:
            console.print(f"[green]Available models:[/green] {', '.join(models[:10])}")
    else:
        console.print("[red]Ollama: Not reachable[/red]")

    from purana_factory.database.base import EntityStatus
    from purana_factory.database.repositories import EntityRepository

    with session_scope() as session:
        repo = EntityRepository(session)
        table = Table(title="Entity Status")
        table.add_column("Status")
        table.add_column("Count")
        for status in EntityStatus:
            count = repo.count_by_status(status)
            table.add_row(status.value, str(count))
        console.print(table)


@app.command("bootstrap")
def bootstrap_cmd() -> None:
    """Load bootstrap mythology entities."""
    setup_logging()
    init_database()
    with session_scope() as session:
        engine = JobEngine(session)
        results = engine.run(pipeline=PipelineType.BOOTSTRAP)
    console.print(f"[green]Bootstrap complete:[/green] {results}")


if __name__ == "__main__":
    app()
