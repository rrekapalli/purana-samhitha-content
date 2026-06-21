# Purana Samhitha Content Factory

Automated Hindu mythology content generation platform for the Purana Samhitha Flutter application.

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -e ".[dev]"

# Initialize database and load bootstrap entities
python main.py --pipeline=bootstrap

# Check system status
python main.py status

# Generate content for all pending entities
python main.py --pipeline=content --all

# Generate for a specific entity
python main.py --pipeline=content --entity-name="Shiva"

# Run full pipeline
python main.py --pipeline=all --all --limit=1
```

## Ollama Configuration

All LLM operations use Ollama at `http://ollama.tailce422e.ts.net:11434/v1`.

Default model: `qwen3:14b` (configurable in `config/settings.yaml`).

## CLI Reference

| Command | Description |
|---------|-------------|
| `--pipeline=all` | Run all pipelines |
| `--pipeline=content` | Entity profiles, relationships, stories, temples, festivals, weapons, places |
| `--pipeline=images` | Image prompts and generation |
| `--pipeline=narration` | Narration scripts and audio |
| `--pipeline=translation` | Translate to target language |
| `--pipeline=validation` | Validate content quality |
| `--pipeline=export` | Export JSON, CSV, SQL |
| `--pipeline=bootstrap` | Load bootstrap entities |
| `--entity-type=DEITY` | Filter by entity type |
| `--entity-name="Krishna"` | Process specific entity |
| `--all` | Process all pending entities |
| `--language=hi` | Target language (en, hi, te, ta, kn, ml, sa) |

## Project Structure

```
purana_factory/
├── config/           # Settings loader
├── database/         # Models, repositories, migrations
├── services/         # Ollama, content, image, audio, translation, export
├── jobs/             # Pipeline orchestration
└── cli/              # Typer CLI
config/settings.yaml  # Configuration
main.py               # Entry point
```

## Tests

```bash
pytest tests/ -v
```

See [Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md) for detailed architecture documentation.
