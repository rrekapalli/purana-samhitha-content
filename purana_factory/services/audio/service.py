"""Audio narration script and TTS generation services."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.config import get_settings
from purana_factory.database.base import JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import AudioRepository, ContentRepository, JobRepository
from purana_factory.services.content.prompts import NARRATION_PROMPT, SYSTEM_PROMPT
from purana_factory.services.content.schemas import NarrationScriptsSchema
from purana_factory.services.ollama import OllamaService


class AudioProviderAdapter(ABC):
    @abstractmethod
    def synthesize(self, text: str, output_path: Path, language: str = "en") -> Path:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class PiperAdapter(AudioProviderAdapter):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    @property
    def name(self) -> str:
        return "piper"

    def synthesize(self, text: str, output_path: Path, language: str = "en") -> Path:
        from subprocess import run

        output_path.parent.mkdir(parents=True, exist_ok=True)
        run(
            ["piper", "--model", self.model_path, "--output_file", str(output_path)],
            input=text.encode("utf-8"),
            check=True,
        )
        return output_path


class KokoroAdapter(AudioProviderAdapter):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "kokoro"

    def synthesize(self, text: str, output_path: Path, language: str = "en") -> Path:
        import requests

        response = requests.post(
            f"{self.base_url}/synthesize",
            json={"text": text, "language": language},
            timeout=300,
        )
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            f.write(response.content)
        return output_path


class CoquiAdapter(AudioProviderAdapter):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "coqui"

    def synthesize(self, text: str, output_path: Path, language: str = "en") -> Path:
        import requests

        response = requests.post(
            f"{self.base_url}/api/tts",
            json={"text": text, "language": language},
            timeout=300,
        )
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            f.write(response.content)
        return output_path


class AudioProviderRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self._providers: dict[str, AudioProviderAdapter] = {}
        cfg = settings.audio.providers
        if cfg.get("piper") and cfg["piper"].enabled and cfg["piper"].model_path:
            self._providers["piper"] = PiperAdapter(cfg["piper"].model_path)
        if cfg.get("kokoro") and cfg["kokoro"].enabled:
            self._providers["kokoro"] = KokoroAdapter(cfg["kokoro"].base_url)
        if cfg.get("coqui") and cfg["coqui"].enabled:
            self._providers["coqui"] = CoquiAdapter(cfg["coqui"].base_url)

    def get(self, name: str) -> AudioProviderAdapter | None:
        return self._providers.get(name)

    def first_available(self) -> AudioProviderAdapter | None:
        for provider in self._providers.values():
            return provider
        return None


class NarrationService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.audio = AudioRepository(session)
        self.content = ContentRepository(session)
        self.jobs = JobRepository(session)

    def generate_scripts(self, entity: Entity, language: str = "en") -> NarrationScriptsSchema:
        job = self.jobs.create(JobType.NARRATION_SCRIPT, entity_id=entity.id, language=language)
        self.jobs.mark_running(job)
        try:
            content = self.content.get_for_entity(entity.id, language)
            description = content.description if content else entity.name
            user_prompt = NARRATION_PROMPT.format(name=entity.name, description=description[:2000])
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, NarrationScriptsSchema, purpose="narration"
            )
            for script in result.scripts:
                self.audio.create(
                    entity_id=entity.id,
                    duration_minutes=script.duration_minutes,
                    script=script.script,
                    language=language,
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.scripts)}))
            logger.info("Generated {} narration scripts for {}", len(result.scripts), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise


class AudioGenerationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audio = AudioRepository(session)
        self.jobs = JobRepository(session)
        self.registry = AudioProviderRegistry()
        self.settings = get_settings()

    def generate_pending(self, limit: int | None = None, provider_name: str | None = None) -> int:
        provider = self.registry.get(provider_name) if provider_name else self.registry.first_available()
        if not provider:
            logger.warning("No audio provider enabled. Scripts stored; enable Piper/Kokoro/Coqui in config.")
            return 0

        pending = self.audio.list_pending(limit=limit)
        count = 0
        for asset in pending:
            job = self.jobs.create(JobType.AUDIO_GENERATION, entity_id=asset.entity_id)
            self.jobs.mark_running(job)
            try:
                output_dir = self.settings.resolve_path(self.settings.paths.generated_audio)
                filename = f"entity_{asset.entity_id}_{asset.duration_minutes}min_{asset.id}.wav"
                output_path = output_dir / filename
                provider.synthesize(asset.script, output_path, asset.language)
                self.audio.update_status(asset, "COMPLETED", str(output_path))
                asset.provider = provider.name
                self.jobs.mark_completed(job, result=str(output_path))
                count += 1
            except Exception as exc:
                self.audio.update_status(asset, "FAILED")
                self.jobs.mark_failed(job, str(exc), retry=True)
        return count
