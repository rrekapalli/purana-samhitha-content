"""Application configuration loaded from YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class OllamaConfig(BaseModel):
    base_url: str = "http://ollama.tailce422e.ts.net:11434"
    api_url: str = "http://ollama.tailce422e.ts.net:11434/v1"
    default_model: str = "qwen3:14b"
    models: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 2


class DatabaseConfig(BaseModel):
    path: str = "purana_samhitha.db"
    echo: bool = False


class GenerationConfig(BaseModel):
    batch_size: int = 10
    max_concurrent_jobs: int = 2


class LanguagesConfig(BaseModel):
    supported: list[str] = Field(
        default_factory=lambda: ["en", "hi", "te", "ta", "kn", "ml", "sa"]
    )
    default: str = "en"


class ImageProviderConfig(BaseModel):
    enabled: bool = False
    base_url: str = ""
    model_path: str = ""


class ImageConfig(BaseModel):
    default_style: str = ""
    providers: dict[str, ImageProviderConfig] = Field(default_factory=dict)


class AudioProviderConfig(BaseModel):
    enabled: bool = False
    base_url: str = ""
    model_path: str = ""


class AudioConfig(BaseModel):
    providers: dict[str, AudioProviderConfig] = Field(default_factory=dict)


class ExportConfig(BaseModel):
    output_dir: str = "generated/exports"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/purana_factory.log"
    rotation: str = "10 MB"
    retention: str = "30 days"


class PathsConfig(BaseModel):
    generated_images: str = "generated/images"
    generated_audio: str = "generated/audio"
    generated_json: str = "generated/json"
    logs: str = "logs"


class Settings(BaseSettings):
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    languages: LanguagesConfig = Field(default_factory=LanguagesConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    project_root: Path = Field(default_factory=lambda: Path.cwd())

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> Settings:
        root = Path.cwd()
        config_path = path or root / "config" / "settings.yaml"
        data: dict[str, Any] = {}
        if config_path.exists():
            with config_path.open(encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
                data = _normalize_yaml(raw)
        settings = cls(**data)
        settings.project_root = root
        return settings

    def resolve_path(self, relative: str) -> Path:
        return self.project_root / relative

    def database_url(self) -> str:
        db_path = self.resolve_path(self.database.path)
        return f"sqlite:///{db_path.as_posix()}"


def _normalize_yaml(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert nested dicts into pydantic-friendly structures."""
    result = dict(raw)
    if "image" in result and "providers" in result["image"]:
        providers = {}
        for name, cfg in result["image"]["providers"].items():
            providers[name] = ImageProviderConfig(**cfg) if isinstance(cfg, dict) else cfg
        result["image"]["providers"] = providers
    if "audio" in result and "providers" in result["audio"]:
        providers = {}
        for name, cfg in result["audio"]["providers"].items():
            providers[name] = AudioProviderConfig(**cfg) if isinstance(cfg, dict) else cfg
        result["audio"]["providers"] = providers
    return result


@lru_cache
def get_settings() -> Settings:
    return Settings.from_yaml()
