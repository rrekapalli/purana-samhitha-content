"""Export entity content from DB into a folder for quality inspection."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from purana_factory.config.settings import get_settings
from purana_factory.database.repositories.entity_repository import slugify
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


def safe_filename(name: str, prefix: str = "", max_len: int = 80) -> str:
    base = slugify(name) or "untitled"
    if prefix:
        base = f"{prefix}_{base}"
    return base[:max_len]


def write_md(path: Path, title: str, sections: dict[str, str | None]) -> None:
    lines = [f"# {title}", ""]
    for heading, body in sections.items():
        if body:
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(body.strip())
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def export_entity(
    entity_name: str,
    output_dir: Path,
    timing_metrics: dict | None = None,
    clear_existing: bool = True,
) -> list[str]:
    get_settings.cache_clear()

    if clear_existing and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    with session_scope() as session:
        entity = EntityRepository(session).get_by_name(entity_name)
        if not entity:
            raise SystemExit(f"{entity_name} not found in database")

        meta_path = output_dir / "entity.json"
        write_json(
            meta_path,
            {
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type.value,
                "status": entity.status.value,
                "sanskrit_name": entity.sanskrit_name,
                "slug": entity.slug,
            },
        )
        written.append(str(meta_path))

        if timing_metrics:
            metrics_path = output_dir / "generation_metrics.json"
            write_json(metrics_path, timing_metrics)
            written.append(str(metrics_path))

        content = ContentRepository(session).get_for_entity(entity.id)
        if content:
            profile_path = output_dir / "profile.md"
            write_md(
                profile_path,
                f"{entity.name} — Entity Profile",
                {
                    "Short Description": content.short_description,
                    "Description": content.description,
                    "Aliases": content.aliases,
                    "Iconography": content.iconography,
                    "Powers": content.powers,
                    "Abilities": content.abilities,
                    "Boons": content.boons,
                    "Curses": content.curses,
                    "Teachings": content.teachings,
                    "Virtues": content.virtues,
                    "Flaws": content.flaws,
                    "Moral Lessons": content.moral_lessons,
                },
            )
            written.append(str(profile_path))

        rels = RelationshipRepository(session).list_for_entity(entity.id)
        rel_data = []
        for rel in rels:
            target = EntityRepository(session).get_by_id(rel.target_entity_id)
            source = EntityRepository(session).get_by_id(rel.source_entity_id)
            rel_data.append(
                {
                    "relationship_type": rel.relationship_type.value,
                    "source_name": source.name if source else None,
                    "target_name": target.name if target else None,
                    "description": rel.description,
                    "source_tradition": rel.source_tradition,
                    "source_reference": rel.source_reference,
                }
            )
        rel_path = output_dir / "relationships.json"
        write_json(rel_path, rel_data)
        written.append(str(rel_path))

        stories = StoryRepository(session).list_for_entity(entity.id)
        story_stats = []
        for story in stories:
            fname = safe_filename(story.title, prefix="story")
            story_path = output_dir / f"{fname}.md"
            narrative_len = len(story.full_narrative or "")
            story_stats.append(
                {"title": story.title, "file": story_path.name, "narrative_chars": narrative_len}
            )
            sections: dict[str, str | None] = {
                "Summary": story.summary,
                "Full Narrative": story.full_narrative,
                "Timeline": story.timeline,
                "Lessons": story.lessons,
                "Concepts": story.concepts,
                "Scriptural Sources": story.scriptural_sources,
            }
            for variant in story.variants:
                key = f"Variant — {variant.tradition}"
                body = variant.variant_narrative or ""
                if variant.variant_title:
                    body = f"**{variant.variant_title}**\n\n{body}"
                if variant.source_reference:
                    body += f"\n\n_Source: {variant.source_reference}_"
                sections[key] = body
            write_md(story_path, story.title, sections)
            written.append(str(story_path))

        stats_path = output_dir / "story_stats.json"
        write_json(stats_path, story_stats)
        written.append(str(stats_path))

        for temple in TempleRepository(session).list_for_entity(entity.id):
            path = output_dir / f"{safe_filename(temple.name, prefix='temple')}.md"
            write_md(
                path,
                temple.name,
                {
                    "Location": temple.location,
                    "Description": temple.description,
                    "Significance": temple.significance,
                    "Pilgrimage Info": temple.pilgrimage_info,
                    "Associated Deities": temple.associated_deities,
                },
            )
            written.append(str(path))

        for festival in FestivalRepository(session).list_for_entity(entity.id):
            path = output_dir / f"{safe_filename(festival.name, prefix='festival')}.md"
            write_md(
                path,
                festival.name,
                {
                    "Description": festival.description,
                    "Rituals": festival.rituals,
                    "Associated Deities": festival.associated_deities,
                    "Calendar": festival.calendar_info,
                },
            )
            written.append(str(path))

        for weapon in WeaponRepository(session).list_for_entity(entity.id):
            path = output_dir / f"{safe_filename(weapon.name, prefix='weapon')}.md"
            write_md(
                path,
                weapon.name,
                {
                    "History": weapon.history,
                    "Powers": weapon.powers,
                    "Owners": weapon.owners,
                    "Associated Stories": weapon.associated_stories,
                },
            )
            written.append(str(path))

        for place in PlaceRepository(session).list_for_entity(entity.id):
            path = output_dir / f"{safe_filename(place.name, prefix='place')}.md"
            write_md(
                path,
                place.name,
                {
                    "Type": place.place_type,
                    "Description": place.description,
                    "Significance": place.significance,
                    "Geography": place.geography,
                },
            )
            written.append(str(path))

        sources = [
            {
                "scripture": s.scripture,
                "citation": s.citation,
                "tradition": s.tradition,
                "notes": s.notes,
            }
            for s in SourceRepository(session).list_for_entity(entity.id)
        ]
        sources_path = output_dir / "source_references.json"
        write_json(sources_path, sources)
        written.append(str(sources_path))

        keywords = [
            {"keyword": k.keyword, "language": k.language}
            for k in KeywordRepository(session).list_for_entity(entity.id)
        ]
        kw_path = output_dir / "search_keywords.json"
        write_json(kw_path, keywords)
        written.append(str(kw_path))

    return written


if __name__ == "__main__":
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "Shiva"
    root = Path(__file__).resolve().parent.parent
    out = root / name.lower()
    files = export_entity(name, out)
    print(f"Exported {len(files)} files to {out}")
    for f in sorted(files):
        print(f"  {Path(f).name}")
