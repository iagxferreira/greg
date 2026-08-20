"""Tests for src.resolver, with the LLM, vector store, and Nominatim fallback mocked."""

import json
from unittest.mock import Mock

from src.models import CountryResult
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


def _mock_llm(content: str):
    return Mock(invoke=Mock(return_value=Mock(content=content)))


def test_no_candidates_returns_no_match(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [])
    monkeypatch.setattr("src.resolver.nominatim_country_fallback", lambda user_input: None)

    result = resolve_country("asdasdasd")

    assert result.matched is False
    assert "No candidates found" in result.reason


def test_happy_path_high_confidence_skips_fallback(monkeypatch):
    fallback = Mock(side_effect=AssertionError("fallback should not be called"))
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr("src.resolver.llm", _mock_llm(json.dumps(LLM_MATCH_RESPONSE)))
    monkeypatch.setattr("src.resolver.nominatim_country_fallback", fallback)

    result = resolve_country("alemania")

    assert result.matched is True
    assert result.name == "Germany"
    assert result.iso2 == "DE"
    assert result.confidence == 0.95
    fallback.assert_not_called()


def test_strips_markdown_code_fences(monkeypatch):
    fenced = "```json\n" + json.dumps(LLM_MATCH_RESPONSE) + "\n```"
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr("src.resolver.llm", _mock_llm(fenced))
    monkeypatch.setattr("src.resolver.nominatim_country_fallback", lambda user_input: None)

    result = resolve_country("alemania")

    assert result.matched is True
    assert result.name == "Germany"


def test_invalid_json_returns_no_match(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr("src.resolver.llm", _mock_llm("not valid json"))
    monkeypatch.setattr("src.resolver.nominatim_country_fallback", lambda user_input: None)

    result = resolve_country("alemania")

    assert result.matched is False
    assert "Failed to parse LLM response" in result.reason


def test_llm_exception_returns_no_match(monkeypatch):
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr(
        "src.resolver.llm", Mock(invoke=Mock(side_effect=RuntimeError("connection refused")))
    )
    monkeypatch.setattr("src.resolver.nominatim_country_fallback", lambda user_input: None)

    result = resolve_country("alemania")

    assert result.matched is False
    assert "LLM error" in result.reason


def test_low_confidence_match_triggers_fallback_and_wins(monkeypatch):
    weak_response = {**LLM_MATCH_RESPONSE, "confidence": 0.55}
    fallback_result = CountryResult(
        matched=True, name="Germany", iso2="DE", confidence=0.6, reason="Nominatim fallback"
    )
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr("src.resolver.llm", _mock_llm(json.dumps(weak_response)))
    monkeypatch.setattr(
        "src.resolver.nominatim_country_fallback", lambda user_input: fallback_result
    )

    result = resolve_country("alemania")

    assert result is fallback_result


def test_no_candidates_falls_back_to_nominatim_on_success(monkeypatch):
    fallback_result = CountryResult(
        matched=True, name="Germany", iso2="DE", confidence=0.6, reason="Nominatim fallback"
    )
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [])
    monkeypatch.setattr(
        "src.resolver.nominatim_country_fallback", lambda user_input: fallback_result
    )

    result = resolve_country("alemania")

    assert result is fallback_result


def test_fallback_failure_keeps_original_low_confidence_result(monkeypatch):
    weak_response = {**LLM_MATCH_RESPONSE, "confidence": 0.55}
    monkeypatch.setattr("src.resolver.search_countries", lambda user_input, k: [CANDIDATE])
    monkeypatch.setattr("src.resolver.llm", _mock_llm(json.dumps(weak_response)))
    monkeypatch.setattr("src.resolver.nominatim_country_fallback", lambda user_input: None)

    result = resolve_country("alemania")

    assert result.matched is True
    assert result.confidence == 0.55
