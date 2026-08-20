"""Tests for src.resolver, with the LLM and vector store mocked out."""

import json
from unittest.mock import Mock

from src.resolver import resolve_country

CANDIDATE = {
    "name": "Germany",
    "iso2": "DE",
    "iso3": "DEU",
    "official_name": "Federal Republic of Germany",
    "capital": "Berlin",
    "region": "Europe",
    "subregion": "Western Europe",
    "content": "All Names: Germany, Deutschland, Alemania",
}

LLM_MATCH_RESPONSE = {
    "matched": True,
    "name": "Germany",
    "official_name": "Federal Republic of Germany",
    "iso2": "DE",
    "iso3": "DEU",
    "capital": "Berlin",
    "region": "Europe",
    "subregion": "Western Europe",
    "confidence": 0.95,
    "reason": "Alemania is the Spanish translation for Germany",
}


def test_no_candidates_returns_no_match(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [])

    result = resolve_country("asdasdasd")

    assert result.matched is False
    assert "No candidates found" in result.reason


def test_happy_path_parses_llm_json(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr(
        "src.resolver.llm",
        Mock(invoke=Mock(return_value=Mock(content=json.dumps(LLM_MATCH_RESPONSE)))),
    )

    result = resolve_country("alemania")

    assert result.matched is True
    assert result.name == "Germany"
    assert result.iso2 == "DE"
    assert result.confidence == 0.95


def test_strips_markdown_code_fences(monkeypatch):
    fenced = "```json\n" + json.dumps(LLM_MATCH_RESPONSE) + "\n```"
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr("src.resolver.llm", Mock(invoke=Mock(return_value=Mock(content=fenced))))

    result = resolve_country("alemania")

    assert result.matched is True
    assert result.name == "Germany"


def test_invalid_json_returns_no_match(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr(
        "src.resolver.llm", Mock(invoke=Mock(return_value=Mock(content="not valid json")))
    )

    result = resolve_country("alemania")

    assert result.matched is False
    assert "Failed to parse LLM response" in result.reason


def test_llm_exception_returns_no_match(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr(
        "src.resolver.llm", Mock(invoke=Mock(side_effect=RuntimeError("connection refused")))
    )

    result = resolve_country("alemania")

    assert result.matched is False
    assert "LLM error" in result.reason
