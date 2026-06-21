# Purana Samhitha Content Factory - Architecture

## Overview

The Purana Samhitha Content Factory is a production-ready Python platform that automatically generates, manages, enriches, validates, translates, narrates, and illustrates Hindu mythology content for the Purana Samhitha Flutter application.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.12+ |
| Database | SQLite with SQLAlchemy 2.x |
| Migrations | Alembic |
| CLI | Typer + Rich |
| Validation | Pydantic |
| LLM | Ollama (qwen3:14b default) |
| Logging | Loguru |
| Retries | Tenacity |

## Ollama Integration

All content generation uses local Ollama models:

- **Base URL**: `http://ollama.tailce422e.ts.net:11434`
- **OpenAI-compatible API**: `http://ollama.tailce422e.ts.net:11434/v1`
- **Models**: qwen3:14b (default), qwen3:30b (large content)

The `OllamaService` provides:
- Connection management via Ollama Python SDK
- OpenAI-compatible `/v1/chat/completions` fallback
- Retry handling with Tenacity
- Structured JSON validation with Pydantic
- Timeout and logging

## Content Pipeline (7 Steps)

1. **Entity Profile** - name, aliases, description, iconography, powers, teachings, sources
2. **Relationships** - FATHER_OF, CONSORT_OF, AVATAR_OF, etc.
3. **Stories** - narratives with tradition variants stored separately
4. **Temples** - pilgrimage sites and sacred places
5. **Festivals** - rituals and associated deities
6. **Weapons** - history, powers, owners
7. **Places** - kingdoms, rivers, mountains

## Image Pipeline

- Generates prompts via Ollama (PORTRAIT, TEMPLE, STORY, WEAPON, FESTIVAL, FAMILY_TREE, KNOWLEDGE_GRAPH)
- Adapter pattern for ComfyUI, Flux, SDXL providers
- Prompts stored in `image_asset` table; files in `generated/images/`

## Narration Pipeline

- Scripts for 2, 5, and 15 minute narrations via Ollama
- TTS adapters: Piper, Kokoro, Coqui
- Audio metadata in `audio_asset` table; files in `generated/audio/`

## Translation Pipeline

Supported languages: en, hi, te, ta, kn, ml, sa

Translated content stored in `language_content` table without overwriting originals.

## Job Engine

Every task tracked in `generation_job` with statuses: PENDING, RUNNING, COMPLETED, FAILED, RETRY.

Supports resumable batch execution and incremental generation.

## Database Schema

Core tables: entity, entity_content, entity_relationship, story, story_variant, temple, festival, weapon, place, concept, image_asset, audio_asset, source_reference, generation_job, generation_log, language_content, search_keyword.

## Export

Exports to `generated/exports/` in JSON, CSV, and SQL formats.

## Quality Rules

- Content derived from Mahabharata, Ramayana, Puranas, Vedas, Upanishads
- Conflicting traditions stored as separate variants
- Source references always preserved
