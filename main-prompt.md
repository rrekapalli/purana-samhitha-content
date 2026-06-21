You are a Senior Python Architect, Data Engineer, AI Engineer, Knowledge Graph Architect, SQLite Expert, Hindu Mythology Researcher, and DevOps Engineer.

Build a complete production-ready Python project called:

PURANA SAMHITHA CONTENT FACTORY

The project will automatically generate, manage, enrich, validate, translate, narrate and illustrate Hindu mythology content for the Purana Samhitha Flutter application.

========================================================
PROJECT OBJECTIVE
=================

Create a fully automated content generation platform.

The system must:

1. Create SQLite database automatically.
2. Create all database tables automatically.
3. Bootstrap mythology entities.
4. Generate mythology content using Ollama.
5. Store generated content in SQLite.
6. Generate relationships.
7. Generate stories.
8. Generate temples.
9. Generate festivals.
10. Generate image prompts.
11. Generate narration scripts.
12. Generate images through image generation APIs.
13. Generate audio narration files.
14. Translate content into multiple languages.
15. Export content.
16. Support resumable job execution.

The system must be capable of generating thousands of mythology entities.

========================================================
TECHNOLOGY STACK
================

Python 3.12+

SQLite

SQLAlchemy 2.x

Alembic

Typer CLI

Pydantic

Ollama Python SDK

Requests

Loguru

Tenacity

Rich

APScheduler

PyYAML

Pillow

pytest

========================================================
SUPPORTED MODELS
================

Content Generation:

qwen3:14b

qwen3:30b

Image Prompt Generation:

qwen3:14b

Narration Script Generation:

qwen3:14b

Translation:

qwen3:14b

Default model:

qwen3:14b

Configurable via YAML.

========================================================
PROJECT STRUCTURE
=================

purana_factory/

config/

database/

database/migrations/

database/models/

database/repositories/

services/

services/ollama/

services/content/

services/image/

services/audio/

services/translation/

services/export/

services/validation/

services/bootstrap/

jobs/

cli/

tests/

generated/

generated/images/

generated/audio/

generated/json/

generated/exports/

logs/

========================================================
CLI DESIGN
==========

Support:

python main.py --pipeline=all

python main.py --pipeline=content

python main.py --pipeline=images

python main.py --pipeline=narration

python main.py --pipeline=translation

python main.py --pipeline=validation

python main.py --pipeline=export

---

python main.py 
--entity-type=DEITY

python main.py 
--entity-type=CHARACTER

python main.py 
--entity-type=SAGE

python main.py 
--entity-type=TEMPLE

---

python main.py 
--entity-name="Shiva"

python main.py 
--entity-name="Krishna"

---

python main.py 
--all

Generate all pending entities.

---

python main.py 
--all 
--language=en

---

python main.py 
--all 
--language=hi

---

python main.py 
--all 
--language=te

---

python main.py 
--all 
--language=sa

========================================================
DATABASE
========

Database name:

purana_samhitha.db

Automatically create database if missing.

========================================================
CORE TABLES
===========

entity

entity_content

entity_relationship

story

story_variant

temple

festival

weapon

place

concept

image_asset

audio_asset

source_reference

generation_job

generation_log

language_content

search_keyword

========================================================
ENTITY TABLE
============

Store all entity types.

Supported entity types:

DEITY

CHARACTER

SAGE

RISHI

DEMON

ASURA

KING

QUEEN

DYNASTY

KINGDOM

TEMPLE

PLACE

MOUNTAIN

RIVER

WEAPON

OBJECT

ANIMAL

VEHICLE

SCRIPTURE

FESTIVAL

EVENT

CONCEPT

AVATAR

========================================================
BOOTSTRAP DATA
==============

System must load bootstrap entities.

Examples:

Shiva

Parvati

Ganesha

Kartikeya

Nandi

Vishnu

Lakshmi

Brahma

Saraswati

Rama

Sita

Lakshmana

Hanuman

Krishna

Radha

Arjuna

Bhishma

Karna

Draupadi

Durga

Kali

Indra

Agni

Varuna

Yama

Kubera

Surya

Chandra

Narada

Prahlada

Dhruva

Garuda

Jatayu

Markandeya

Vasishta

Vishwamitra

Brihaspati

Shukracharya

and hundreds more.

Initially insert as PENDING.

========================================================
CONTENT GENERATION PIPELINE
===========================

Pipeline Step 1

Generate Entity Profile.

Generate:

name

aliases

sanskrit_name

description

short_description

iconography

powers

abilities

boons

curses

teachings

virtues

flaws

moral_lessons

search_keywords

primary_sources

========================================================
Pipeline Step 2

Generate Relationships.

Generate all known relationships.

Examples:

FATHER_OF

MOTHER_OF

CHILD_OF

CONSORT_OF

DISCIPLE_OF

GURU_OF

ALLY_OF

ENEMY_OF

AVATAR_OF

INCARNATION_OF

USES

RIDES

OWNS

RULES

RESIDES_AT

ASSOCIATED_WITH

PARTICIPATED_IN

WORSHIPPED_AT

========================================================
Pipeline Step 3

Generate Stories.

Generate:

summary

full_narrative

timeline

lessons

concepts

scriptural_sources

variants

========================================================
Pipeline Step 4

Generate Temples.

Generate:

major temples

pilgrimage sites

sacred places

========================================================
Pipeline Step 5

Generate Festivals.

Generate:

festival descriptions

rituals

associated deities

========================================================
Pipeline Step 6

Generate Weapons.

Generate:

weapon history

powers

owners

associated stories

========================================================
Pipeline Step 7

Generate Places.

Generate:

kingdoms

rivers

mountains

sacred regions

========================================================
IMAGE PIPELINE
==============

Generate image prompts.

Store prompts in image_asset table.

Generate image types:

PORTRAIT

TEMPLE

STORY

WEAPON

FESTIVAL

FAMILY_TREE

KNOWLEDGE_GRAPH

Image style:

Ancient Hindu manuscript

Temple mural

Tanjore painting

Mythology encyclopedia illustration

Highly detailed

========================================================
IMAGE GENERATION PROVIDERS
==========================

Architecture must support:

ComfyUI

Flux

SDXL

Future providers

Use adapter pattern.

========================================================
NARRATION PIPELINE
==================

Generate:

2 minute narration

5 minute narration

15 minute narration

Store scripts in database.

Support:

Piper

Kokoro

Coqui

Store generated audio metadata.

========================================================
TRANSLATION PIPELINE
====================

Supported languages:

en

hi

te

ta

kn

ml

sa

Store translated content separately.

Do not overwrite original content.

========================================================
EXPORT PIPELINE
===============

Support:

JSON

CSV

SQL

Generate exports into:

generated/exports/

========================================================
OLLAMA SERVICE
==============

Create reusable Ollama service.

Features:

Connection management

Retry handling

Structured JSON validation

Timeout handling

Logging

Configuration driven

========================================================
JOB ENGINE
==========

Every generation task must be tracked.

Statuses:

PENDING

RUNNING

COMPLETED

FAILED

RETRY

Support resumable execution.

Support batch execution.

Support incremental generation.

========================================================
QUALITY RULES
=============

Generate complete production-ready code.

Generate all SQLAlchemy models.

Generate all repositories.

Generate all services.

Generate CLI.

Generate tests.

Generate migrations.

Generate configuration system.

Generate logging.

Generate validation.

Generate error handling.

No placeholders.

No TODOs.

No stubs.

No mock implementations.

Code must be executable.

========================================================
CONTENT GENERATION RULES
========================

Content must be derived from:

Mahabharata

Ramayana

Bhagavata Purana

Shiva Purana

Vishnu Purana

Devi Bhagavatam

Skanda Purana

Markandeya Purana

Padma Purana

Garuda Purana

Narada Purana

Vedas

Upanishads

When multiple traditions exist:

Store variants separately.

Never merge conflicting traditions.

Always preserve source references.

========================================================
FINAL DELIVERABLE
=================

Generate the complete Python project with all files, folders, models, migrations, repositories, services, pipelines, CLI commands, tests and documentation required to run the Purana Samhitha Content Factory locally using Ollama.
