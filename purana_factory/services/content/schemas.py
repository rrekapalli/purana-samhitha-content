"""Pydantic schemas for LLM structured output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EntityProfileSchema(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    sanskrit_name: str | None = None
    description: str
    short_description: str
    iconography: str | None = None
    powers: list[str] = Field(default_factory=list)
    abilities: list[str] = Field(default_factory=list)
    boons: list[str] = Field(default_factory=list)
    curses: list[str] = Field(default_factory=list)
    teachings: list[str] = Field(default_factory=list)
    virtues: list[str] = Field(default_factory=list)
    flaws: list[str] = Field(default_factory=list)
    moral_lessons: list[str] = Field(default_factory=list)
    search_keywords: list[str] = Field(default_factory=list)
    primary_sources: list[str] = Field(default_factory=list)


class RelationshipItem(BaseModel):
    target_name: str
    relationship_type: str
    description: str | None = None
    source_tradition: str | None = None
    source_reference: str | None = None


class RelationshipsSchema(BaseModel):
    relationships: list[RelationshipItem] = Field(default_factory=list)


class StoryVariantItem(BaseModel):
    tradition: str
    variant_title: str | None = None
    variant_narrative: str | None = None
    source_reference: str | None = None


class StoryItem(BaseModel):
    title: str
    summary: str
    full_narrative: str
    timeline: str | None = None
    lessons: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    scriptural_sources: list[str] = Field(default_factory=list)
    variants: list[StoryVariantItem] = Field(default_factory=list)


class StoriesSchema(BaseModel):
    stories: list[StoryItem] = Field(default_factory=list)


class TempleItem(BaseModel):
    name: str
    location: str | None = None
    description: str | None = None
    significance: str | None = None
    pilgrimage_info: str | None = None
    associated_deities: list[str] = Field(default_factory=list)


class TemplesSchema(BaseModel):
    temples: list[TempleItem] = Field(default_factory=list)


class FestivalItem(BaseModel):
    name: str
    description: str | None = None
    rituals: list[str] = Field(default_factory=list)
    associated_deities: list[str] = Field(default_factory=list)
    calendar_info: str | None = None


class FestivalsSchema(BaseModel):
    festivals: list[FestivalItem] = Field(default_factory=list)


class WeaponItem(BaseModel):
    name: str
    history: str | None = None
    powers: list[str] = Field(default_factory=list)
    owners: list[str] = Field(default_factory=list)
    associated_stories: list[str] = Field(default_factory=list)


class WeaponsSchema(BaseModel):
    weapons: list[WeaponItem] = Field(default_factory=list)


class PlaceItem(BaseModel):
    name: str
    place_type: str | None = None
    description: str | None = None
    significance: str | None = None
    geography: str | None = None


class PlacesSchema(BaseModel):
    places: list[PlaceItem] = Field(default_factory=list)


class ImagePromptItem(BaseModel):
    image_type: str
    prompt: str
    style: str | None = None


class ImagePromptsSchema(BaseModel):
    prompts: list[ImagePromptItem] = Field(default_factory=list)


class NarrationScriptSchema(BaseModel):
    duration_minutes: int
    script: str


class NarrationScriptsSchema(BaseModel):
    scripts: list[NarrationScriptSchema] = Field(default_factory=list)


class TranslationItem(BaseModel):
    field_name: str
    translated_text: str


class TranslationSchema(BaseModel):
    translations: list[TranslationItem] = Field(default_factory=list)
