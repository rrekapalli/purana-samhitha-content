"""Image prompt and generation services with adapter pattern."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from purana_factory.config import get_settings
from purana_factory.database.base import ImageType, JobType
from purana_factory.database.models.entity import Entity
from purana_factory.database.repositories import ImageRepository, JobRepository
from purana_factory.services.content.prompts import IMAGE_PROMPT_TEMPLATE, SYSTEM_PROMPT
from purana_factory.services.content.schemas import ImagePromptsSchema
from purana_factory.services.ollama import OllamaService


class ImageProviderAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: Path, style: str | None = None) -> Path:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class ComfyUIAdapter(ImageProviderAdapter):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "comfyui"

    def generate(self, prompt: str, output_path: Path, style: str | None = None) -> Path:
        import requests

        full_prompt = f"{prompt}. Style: {style}" if style else prompt
        workflow = {
            "prompt": full_prompt,
            "output_path": str(output_path),
        }
        response = requests.post(f"{self.base_url}/prompt", json=workflow, timeout=300)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        return output_path


class FluxAdapter(ImageProviderAdapter):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "flux"

    def generate(self, prompt: str, output_path: Path, style: str | None = None) -> Path:
        import requests

        full_prompt = f"{prompt}. Style: {style}" if style else prompt
        response = requests.post(
            f"{self.base_url}/generate",
            json={"prompt": full_prompt},
            timeout=300,
        )
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            f.write(response.content)
        return output_path


class SDXLAdapter(ImageProviderAdapter):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "sdxl"

    def generate(self, prompt: str, output_path: Path, style: str | None = None) -> Path:
        import requests

        full_prompt = f"{prompt}. Style: {style}" if style else prompt
        response = requests.post(
            f"{self.base_url}/sdapi/v1/txt2img",
            json={"prompt": full_prompt, "steps": 30, "width": 1024, "height": 1024},
            timeout=300,
        )
        response.raise_for_status()
        import base64

        images = response.json().get("images", [])
        if not images:
            raise RuntimeError("SDXL returned no images")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            f.write(base64.b64decode(images[0]))
        return output_path


class ImageProviderRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self._providers: dict[str, ImageProviderAdapter] = {}
        cfg = settings.image.providers
        if cfg.get("comfyui") and cfg["comfyui"].enabled:
            self._providers["comfyui"] = ComfyUIAdapter(cfg["comfyui"].base_url)
        if cfg.get("flux") and cfg["flux"].enabled:
            self._providers["flux"] = FluxAdapter(cfg["flux"].base_url)
        if cfg.get("sdxl") and cfg["sdxl"].enabled:
            self._providers["sdxl"] = SDXLAdapter(cfg["sdxl"].base_url)

    def get(self, name: str) -> ImageProviderAdapter | None:
        return self._providers.get(name)

    def first_available(self) -> ImageProviderAdapter | None:
        for provider in self._providers.values():
            return provider
        return None

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())


class ImagePromptService:
    def __init__(self, session: Session, ollama: OllamaService | None = None) -> None:
        self.session = session
        self.ollama = ollama or OllamaService()
        self.images = ImageRepository(session)
        self.jobs = JobRepository(session)
        self.settings = get_settings()

    def generate_prompts(self, entity: Entity) -> ImagePromptsSchema:
        job = self.jobs.create(JobType.IMAGE_PROMPT, entity_id=entity.id)
        self.jobs.mark_running(job)
        try:
            user_prompt = IMAGE_PROMPT_TEMPLATE.format(name=entity.name)
            result = self.ollama.generate_validated(
                SYSTEM_PROMPT, user_prompt, ImagePromptsSchema, purpose="image_prompt"
            )
            default_style = self.settings.image.default_style
            for item in result.prompts:
                try:
                    image_type = ImageType(item.image_type)
                except ValueError:
                    image_type = ImageType.PORTRAIT
                self.images.create(
                    entity_id=entity.id,
                    image_type=image_type,
                    prompt=item.prompt,
                    style=item.style or default_style,
                )
            self.jobs.mark_completed(job, result=json.dumps({"count": len(result.prompts)}))
            logger.info("Generated {} image prompts for {}", len(result.prompts), entity.name)
            return result
        except Exception as exc:
            self.jobs.mark_failed(job, str(exc), retry=True)
            raise


class ImageGenerationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.images = ImageRepository(session)
        self.jobs = JobRepository(session)
        self.registry = ImageProviderRegistry()
        self.settings = get_settings()

    def generate_pending(self, limit: int | None = None, provider_name: str | None = None) -> int:
        provider = self.registry.get(provider_name) if provider_name else self.registry.first_available()
        if not provider:
            logger.warning("No image provider enabled. Prompts stored; enable ComfyUI/Flux/SDXL in config.")
            return 0

        pending = self.images.list_pending(limit=limit)
        count = 0
        for asset in pending:
            job = self.jobs.create(JobType.IMAGE_GENERATION, entity_id=asset.entity_id)
            self.jobs.mark_running(job)
            try:
                output_dir = self.settings.resolve_path(self.settings.paths.generated_images)
                filename = f"entity_{asset.entity_id}_{asset.image_type.value}_{asset.id}.png"
                output_path = output_dir / filename
                provider.generate(asset.prompt, output_path, asset.style)
                self.images.update_status(asset, "COMPLETED", str(output_path))
                asset.provider = provider.name
                self.jobs.mark_completed(job, result=str(output_path))
                count += 1
            except Exception as exc:
                self.images.update_status(asset, "FAILED")
                self.jobs.mark_failed(job, str(exc), retry=True)
        return count
