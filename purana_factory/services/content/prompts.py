"""Content generation prompts."""

STORYBOOK_STYLE = """
WRITING STYLE (apply to ALL narrative text — descriptions, stories, histories):
- Write for children aged 8 and above — warm, wonder-filled, and easy to follow
- Use the voice of a children's storybook: flowing sentences, gentle drama, vivid imagery
- Sprinkle somewhat flowery, poetic language — golden sunbeams, whispering winds, hearts full of courage
- Tell stories as adventures with characters who feel, speak, and act — NOT like a textbook or documentary
- Include elaborate descriptions: how things looked, sounded, and felt; origin tales woven into the narrative
- Use dialogue where natural — let gods, sages, and heroes speak in simple, memorable lines
- NEVER use dry bullet-point lists inside narrative fields — write full paragraphs only
- Avoid academic phrases like "it is documented that", "historically", "according to scholars"
- End each story with a gentle moral woven into the closing lines, not as a separate lecture
- Be scripturally faithful to Mahabharata, Ramayana, Puranas, Vedas, and Upanishads
- When traditions differ, tell each version as its own story — never merge conflicting accounts
"""

SYSTEM_PROMPT = f"""You are a beloved storyteller of Hindu mythology, writing for children aged 8 and above.
Your tales come from authentic sources: Mahabharata, Ramayana, Bhagavata Purana, Shiva Purana,
Vishnu Purana, Devi Bhagavatam, Skanda Purana, Markandeya Purana, Padma Purana, Garuda Purana,
Narada Purana, Vedas, and Upanishads.

{STORYBOOK_STYLE}

Technical rules:
- Return valid JSON only — no markdown fences, no commentary outside JSON
- Fill every text field with rich, maximum-length content — never leave fields sparse or stubby
- Cite sources in scriptural_sources fields, not woven into story prose as footnotes
"""

MIN_STORY_NARRATIVE_CHARS = 2000
MIN_STORY_COUNT = 5
PROMPT_STORY_MIN_CHARS = 3000

ENTITY_PROFILE_PROMPT = """Write a rich profile for the Hindu mythology figure: {name} (type: {entity_type}).

Use children's storybook language — vivid, warm, wonder-filled — NOT documentary or encyclopedia tone.
The description must be a flowing narrative portrait (600+ words) that a child would love to read aloud.

Return JSON:
{{
  "name": "string",
  "aliases": ["string"],
  "sanskrit_name": "string or null",
  "description": "flowing narrative portrait, 600+ words, storybook style",
  "short_description": "2-3 inviting sentences a child would enjoy",
  "iconography": "vivid paragraph describing appearance, symbols, and what each means — storybook style",
  "powers": ["each power as a short vivid phrase, not a dry list"],
  "abilities": ["each ability as a short vivid phrase"],
  "boons": ["boons given or received, with brief context"],
  "curses": ["curses given or received, with brief context"],
  "teachings": ["teachings as memorable lines or short phrases"],
  "virtues": ["virtues as vivid phrases"],
  "flaws": ["flaws described gently and honestly"],
  "moral_lessons": ["lessons children can carry in their hearts"],
  "search_keywords": ["relevant search terms"],
  "primary_sources": ["scripture names with chapter/section references"]
}}
"""

RELATIONSHIPS_PROMPT = """List all known relationships for: {name}.

Return JSON:
{{
  "relationships": [
    {{
      "target_name": "related entity name",
      "relationship_type": "FATHER_OF|MOTHER_OF|CHILD_OF|CONSORT_OF|DISCIPLE_OF|GURU_OF|ALLY_OF|ENEMY_OF|AVATAR_OF|INCARNATION_OF|USES|RIDES|OWNS|RULES|RESIDES_AT|ASSOCIATED_WITH|PARTICIPATED_IN|WORSHIPPED_AT",
      "description": "2-4 sentences in storybook style explaining the bond",
      "source_tradition": "tradition name if applicable",
      "source_reference": "scripture citation"
    }}
  ]
}}
"""

STORIES_PROMPT = """Tell the greatest stories of {name} for children aged 8 and above.

Generate at least {min_story_count} major stories. Each story must feel like a chapter from a children's mythology storybook.

CRITICAL LENGTH RULE: Each "full_narrative" MUST be at least {min_chars} characters of continuous story prose.
Count carefully — short chapters will be rejected. Aim for 2500–3500 characters per story.
Write long, flowing chapters — origin tales, adventures, dialogue, vivid scenes, and gentle morals woven into the ending.
Do NOT write summaries disguised as narratives. Do NOT use bullet points inside full_narrative.

Each story should include:
- How the tale began (origin and setting painted with wonder)
- What happened step by step (characters speak, act, and feel)
- A vivid climax and a heartwarming or thoughtful ending
- At least 4-6 paragraphs of rich prose per story

Return JSON:
{{
  "stories": [
    {{
      "title": "evocative story title",
      "summary": "3-4 inviting sentences — a teaser a child would love",
      "full_narrative": "COMPLETE storybook chapter, minimum {min_chars} characters, flowing paragraphs only",
      "timeline": "when in cosmic or earthly time, told simply",
      "lessons": ["moral lessons as short memorable phrases"],
      "concepts": ["philosophical ideas named simply for children"],
      "scriptural_sources": ["scripture citations"],
      "variants": [
        {{
          "tradition": "tradition name",
          "variant_title": "title of alternate version",
          "variant_narrative": "full alternate version, minimum 800 characters, storybook style",
          "source_reference": "citation"
        }}
      ]
    }}
  ]
}}
"""

STORIES_BATCH_PROMPT = """Tell exactly 2 complete stories about {name} for children aged 8 and above.

Stories to tell in THIS batch (one full chapter each):
{story_topics}

Each story must feel like a chapter from a children's mythology storybook.

CRITICAL LENGTH RULE: Each "full_narrative" MUST be at least {min_chars} characters of continuous story prose.
Count carefully — short chapters will be rejected. Aim for 2500–3500 characters per story.
Write long, flowing chapters — origin tales, adventures, dialogue, vivid scenes, and gentle morals woven into the ending.
Do NOT write summaries disguised as narratives. Do NOT use bullet points inside full_narrative.

Return JSON with exactly 2 stories:
{{
  "stories": [
    {{
      "title": "evocative story title",
      "summary": "3-4 inviting sentences",
      "full_narrative": "COMPLETE storybook chapter, minimum {min_chars} characters, flowing paragraphs only",
      "timeline": "when in cosmic or earthly time, told simply",
      "lessons": ["moral lessons as short memorable phrases"],
      "concepts": ["philosophical ideas named simply for children"],
      "scriptural_sources": ["scripture citations"],
      "variants": [
        {{
          "tradition": "tradition name",
          "variant_title": "title of alternate version",
          "variant_narrative": "full alternate version, minimum 800 characters, storybook style",
          "source_reference": "citation"
        }}
      ]
    }}
  ]
}}
"""
TEMPLES_PROMPT = """Describe the sacred temples and pilgrimage places linked to {name}.

Write descriptions in warm storybook style — how pilgrims feel, what wonders they see — not dry guidebook text.
Each description field should be a full paragraph (80+ words).

Return JSON:
{{
  "temples": [
    {{
      "name": "temple name",
      "location": "city, state, country",
      "description": "vivid paragraph — what the temple looks like and feels like",
      "significance": "why this place matters, told as a short tale",
      "pilgrimage_info": "what pilgrims do and experience",
      "associated_deities": ["deity names"]
    }}
  ]
}}
"""

FESTIVALS_PROMPT = """Describe festivals celebrated for {name}.

Write as if inviting a child to join the celebration — colors, sounds, joy, and meaning.
Each description should be a full paragraph in storybook style.

Return JSON:
{{
  "festivals": [
    {{
      "name": "festival name",
      "description": "vivid paragraph about the festival atmosphere and meaning",
      "rituals": ["each ritual as a short vivid phrase or sentence"],
      "associated_deities": ["deity names"],
      "calendar_info": "when celebrated, told simply"
    }}
  ]
}}
"""

WEAPONS_PROMPT = """Tell the legendary tales of weapons associated with {name}.

Each history field must be a full origin story (150+ words) in children's storybook style.

Return JSON:
{{
  "weapons": [
    {{
      "name": "weapon name",
      "history": "origin story — how the weapon came to be, 150+ words, storybook prose",
      "powers": ["powers described vividly"],
      "owners": ["owners with brief context"],
      "associated_stories": ["story titles or brief tale references"]
    }}
  ]
}}
"""

PLACES_PROMPT = """Describe the sacred places, kingdoms, rivers, and mountains linked to {name}.

Paint each place with wonder — what a child would see, hear, and feel there.
Each description must be a full paragraph (80+ words).

Return JSON:
{{
  "places": [
    {{
      "name": "place name",
      "place_type": "KINGDOM|RIVER|MOUNTAIN|REGION|CITY",
      "description": "vivid paragraph in storybook style",
      "significance": "why this place is sacred, told as a short tale",
      "geography": "geographic details woven into readable prose"
    }}
  ]
}}
"""

IMAGE_PROMPT_TEMPLATE = """Generate image prompts for Hindu mythology entity: {name}.

Image types: PORTRAIT, TEMPLE, STORY, WEAPON, FESTIVAL, FAMILY_TREE, KNOWLEDGE_GRAPH.
Style: Ancient Hindu manuscript, temple mural, Tanjore painting, mythology encyclopedia illustration, highly detailed.

Return JSON:
{{
  "prompts": [
    {{
      "image_type": "PORTRAIT",
      "prompt": "detailed image generation prompt",
      "style": "art style description"
    }}
  ]
}}
"""

NARRATION_PROMPT = """Generate narration scripts for Hindu mythology entity: {name}.
Entity description: {description}

Write in warm children's storybook voice. Generate scripts for 2, 5, and 15 minute narrations.

Return JSON:
{{
  "scripts": [
    {{
      "duration_minutes": 2,
      "script": "full narration script"
    }},
    {{
      "duration_minutes": 5,
      "script": "full narration script"
    }},
    {{
      "duration_minutes": 15,
      "script": "full narration script"
    }}
  ]
}}
"""

TRANSLATION_PROMPT = """Translate the following Hindu mythology content from English to {target_language}.
Preserve Sanskrit terms where appropriate. Keep the warm storybook tone for children.
Return JSON only.

Fields to translate:
{fields_json}

Return JSON:
{{
  "translations": [
    {{
      "field_name": "field name",
      "translated_text": "translated content"
    }}
  ]
}}
"""
