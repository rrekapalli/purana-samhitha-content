"""Story generation service."""

from __future__ import annotations

import json

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.database.base import JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import JobRepository, StoryRepository
from purana_factory.services.content.prompts import (
    MIN_STORY_COUNT,
    MIN_STORY_NARRATIVE_CHARS,
    PROMPT_STORY_MIN_CHARS,
    STORIES_BATCH_PROMPT,
    SYSTEM_PROMPT,
)
from purana_factory.services.content.schemas import StoriesSchema, StoryItem
from purana_factory.services.ollama import OllamaService, OllamaServiceError

MAX_STORY_RETRIES = 3
STORY_BATCH_TOPICS = [
    [
        "How the sacred river Ganga descended from heaven onto Shiva's matted hair",
        "Shiva's magnificent cosmic dance as Nataraja, Lord of Dance",
    ],
    [
        "How Shiva and Parvati met, courted, and were united in marriage",
        "Shiva drinking the deadly poison Halahala during Samudra Manthan",
    ],
    [
        "The birth of Ganesha and how Shiva gave him an elephant head",
        "Shiva granting boons to devoted souls like Markandeya and Kannappa",
    ],
]


def _list_to_text(items: list[str] | None) -> str | None:
    if not items:
        return None
    return "\n".join(f"- {item}" for item in items)


def _validate_stories(stories: list[StoryItem]) -> list[str]:
    issues: list[str] = []
    if len(stories) < MIN_STORY_COUNT:
        issues.append(f"expected at least {MIN_STORY_COUNT} stories, got {len(stories)}")
    for story in stories:
        length = len(story.full_narrative or "")
        if length < MIN_STORY_NARRATIVE_CHARS:
            issues.append(
                f"story '{story.title}' narrative too short: {length} chars "
                f"(minimum {MIN_STORY_NARRATIVE_CHARS})"
            )
    return issues


class StoryService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.stories = StoryRepository(session)
        self.jobs = JobRepository(session)

    def _generate_batch(self, entity: Entity, topics: list[str]) -> list[StoryItem]:
        topics_text = "\n".join(f"- {t}" for t in topics)
        user_prompt = STORIES_BATCH_PROMPT.format(
            name=entity.name,
            story_topics=topics_text,
            min_chars=PROMPT_STORY_MIN_CHARS,
        )
        for attempt in range(1, MAX_STORY_RETRIES + 1):
            try:
                result = self.ollama.generate_validated(
                    SYSTEM_PROMPT, user_prompt, StoriesSchema, purpose="content"
                )
                batch_issues = [
                    f"'{s.title}' ({len(s.full_narrative)} chars)"
                    for s in result.stories
                    if len(s.full_narrative or "") < MIN_STORY_NARRATIVE_CHARS
                ]
                if batch_issues:
                    logger.warning(
                        "Batch stories too short on attempt {}/{}: {}",
                        attempt,
                        MAX_STORY_RETRIES,
                        "; ".join(batch_issues),
                    )
                    if attempt < MAX_STORY_RETRIES:
                        continue
                    raise ValueError("Stories too short: " + "; ".join(batch_issues))
                return result.stories
            except (OllamaServiceError, ValueError) as exc:
                logger.warning(
                    "Story batch attempt {}/{} failed for {}: {}",
                    attempt,
                    MAX_STORY_RETRIES,
                    entity.name,
                    exc,
                )
        raise ValueError(f"Story batch failed after {MAX_STORY_RETRIES} attempts")

    def _generate_all_stories(self, entity: Entity) -> list[StoryItem]:
        all_stories: list[StoryItem] = []
        for batch_topics in STORY_BATCH_TOPICS:
            batch_stories = self._generate_batch(entity, batch_topics)
            all_stories.extend(batch_stories)
            logger.info(
                "Batch generated {} stories for {} (total so far: {})",
                len(batch_stories),
                entity.name,
                len(all_stories),
            )
        return all_stories

    def generate(self, entity: Entity, language: str = "en") -> StoriesSchema:
        job = self.jobs.create(JobType.STORIES, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            self.stories.delete_for_entity(entity.id)

            all_stories = self._generate_all_stories(entity)
            issues = _validate_stories(all_stories)
            if issues:
                raise ValueError("Story validation failed: " + "; ".join(issues))

            result = StoriesSchema(stories=all_stories)

            for story_data in result.stories:
                story = self.stories.create(
                    entity.id,
                    {
                        "title": story_data.title,
                        "summary": story_data.summary,
                        "full_narrative": story_data.full_narrative,
                        "timeline": story_data.timeline,
                        "lessons": _list_to_text(story_data.lessons),
                        "concepts": _list_to_text(story_data.concepts),
                        "scriptural_sources": _list_to_text(story_data.scriptural_sources),
                    },
                    language=language,
                )
                for variant in story_data.variants:
                    self.stories.add_variant(
                        story.id,
                        {
                            "tradition": variant.tradition,
                            "variant_title": variant.variant_title,
                            "variant_narrative": variant.variant_narrative,
                            "source_reference": variant.source_reference,
                        },
                    )

            narrative_lengths = [len(s.full_narrative) for s in result.stories]
            self.jobs.mark_completed(
                job,
                result=json.dumps(
                    {
                        "count": len(result.stories),
                        "narrative_lengths": narrative_lengths,
                        "min_length": min(narrative_lengths),
                    }
                ),
            )
            logger.info(
                "Generated {} stories for {} (min narrative length: {} chars)",
                len(result.stories),
                entity.name,
                min(narrative_lengths),
            )
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise
