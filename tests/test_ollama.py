"""Ollama service tests."""

import json
from unittest.mock import MagicMock, patch

import pytest

from purana_factory.services.ollama.service import OllamaService, OllamaServiceError


def test_parse_json_plain():
    data = OllamaService.parse_json('{"name": "Shiva"}')
    assert data["name"] == "Shiva"


def test_parse_json_markdown_fence():
    raw = '```json\n{"name": "Vishnu"}\n```'
    data = OllamaService.parse_json(raw)
    assert data["name"] == "Vishnu"


def test_parse_json_invalid():
    with pytest.raises(OllamaServiceError):
        OllamaService.parse_json("not json at all")


@patch("purana_factory.services.ollama.service.Client")
def test_chat(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.chat.return_value = {"message": {"content": "Hello"}}

    service = OllamaService()
    result = service.chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello"
    mock_client.chat.assert_called_once()
