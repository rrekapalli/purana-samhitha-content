"""Ollama LLM integration service."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

import requests
from loguru import logger
from ollama import Client
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from purana_factory.config import get_settings

T = TypeVar("T", bound=BaseModel)


class OllamaServiceError(Exception):
    pass


class OllamaService:
    """Reusable Ollama service with retry, timeout, and JSON validation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.host = self.settings.ollama.base_url
        self.api_url = self.settings.ollama.api_url.rstrip("/")
        self.client = Client(host=self.host, timeout=self.settings.ollama.timeout_seconds)

    def _resolve_model(self, purpose: str | None = None) -> str:
        models = self.settings.ollama.models
        if purpose and purpose in models:
            return models[purpose]
        return self.settings.ollama.default_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        purpose: str | None = None,
        format_json: bool = False,
    ) -> str:
        resolved_model = model or self._resolve_model(purpose)
        logger.debug("Ollama chat request model={} messages={}", resolved_model, len(messages))
        try:
            options: dict[str, Any] = {}
            if format_json:
                options["format"] = "json"
            response = self.client.chat(
                model=resolved_model,
                messages=messages,
                options=options if options else None,
            )
            content = response["message"]["content"]
            logger.debug("Ollama response length={}", len(content))
            return content
        except Exception as exc:
            logger.error("Ollama chat failed: {}", exc)
            raise OllamaServiceError(f"Ollama chat failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def chat_openai_compatible(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        purpose: str | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Use OpenAI-compatible /v1/chat/completions endpoint."""
        resolved_model = model or self._resolve_model(purpose)
        url = f"{self.api_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.settings.ollama.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.error("Ollama OpenAI API failed: {}", exc)
            raise OllamaServiceError(f"Ollama OpenAI API failed: {exc}") from exc

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        purpose: str | None = None,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = self.chat(messages, model=model, purpose=purpose, format_json=True)
        return self.parse_json(raw)

    def generate_validated(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        model: str | None = None,
        purpose: str | None = None,
    ) -> T:
        data = self.generate_json(system_prompt, user_prompt, model=model, purpose=purpose)
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            logger.error("JSON validation failed: {}", exc)
            raise OllamaServiceError(f"Response validation failed: {exc}") from exc

    @staticmethod
    def _repair_json(text: str) -> str:
        """Fix common LLM JSON issues such as trailing commas."""
        return re.sub(r",(\s*[}\]])", r"\1", text)

    @staticmethod
    def parse_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        candidates = [text, OllamaService._repair_json(text)]
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            blob = match.group()
            for candidate in [blob, OllamaService._repair_json(blob)]:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
        raise OllamaServiceError("Failed to parse JSON from Ollama response")

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as exc:
            logger.warning("Ollama health check failed: {}", exc)
            return False

    def list_models(self) -> list[str]:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as exc:
            logger.error("Failed to list Ollama models: {}", exc)
            return []
