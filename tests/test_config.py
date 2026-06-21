"""Configuration tests."""

from pathlib import Path

from purana_factory.config.settings import Settings


def test_settings_from_yaml():
    settings = Settings.from_yaml()
    assert settings.ollama.base_url == "http://ollama.tailce422e.ts.net:11434"
    assert settings.ollama.api_url == "http://ollama.tailce422e.ts.net:11434/v1"
    assert settings.ollama.default_model == "qwen3:14b"
    assert "en" in settings.languages.supported
    assert settings.database.path == "purana_samhitha.db"


def test_database_url():
    settings = Settings.from_yaml()
    url = settings.database_url()
    assert url.startswith("sqlite:///")
    assert "purana_samhitha.db" in url


def test_resolve_path():
    settings = Settings.from_yaml()
    path = settings.resolve_path("generated/images")
    assert isinstance(path, Path)
