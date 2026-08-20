"""Tests for src.api, with resolve_country mocked out (no real Ollama/Postgres calls)."""

from unittest.mock import Mock

from fastapi.testclient import TestClient

from src.api import app
from src.models import CountryResult

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_resolve_returns_matched_result(monkeypatch):
    result = CountryResult(
        matched=True,
        name="Germany",
        official_name="Federal Republic of Germany",
        iso2="DE",
        iso3="DEU",
        capital="Berlin",
        region="Europe",
        subregion="Western Europe",
        confidence=0.95,
        reason="Alemania is the Spanish translation for Germany",
    )
    resolve_mock = Mock(return_value=result)
    monkeypatch.setattr("src.api.resolve_country", resolve_mock)

    response = client.get("/v1/countries/resolve", params={"q": "alemania"})

    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["name"] == "Germany"
    assert body["iso2"] == "DE"
    assert body["confidence"] == 0.95
    resolve_mock.assert_called_once_with("alemania", k=5)


def test_resolve_passes_custom_k(monkeypatch):
    resolve_mock = Mock(return_value=CountryResult.no_match())
    monkeypatch.setattr("src.api.resolve_country", resolve_mock)

    client.get("/v1/countries/resolve", params={"q": "alemania", "k": 3})

    resolve_mock.assert_called_once_with("alemania", k=3)


def test_resolve_strips_surrounding_whitespace(monkeypatch):
    resolve_mock = Mock(return_value=CountryResult.no_match())
    monkeypatch.setattr("src.api.resolve_country", resolve_mock)

    client.get("/v1/countries/resolve", params={"q": "  alemania  "})

    resolve_mock.assert_called_once_with("alemania", k=5)


def test_resolve_blank_query_returns_400(monkeypatch):
    resolve_mock = Mock(side_effect=AssertionError("resolve_country should not be called"))
    monkeypatch.setattr("src.api.resolve_country", resolve_mock)

    response = client.get("/v1/countries/resolve", params={"q": "   "})

    assert response.status_code == 400
    resolve_mock.assert_not_called()


def test_resolve_missing_query_returns_422():
    response = client.get("/v1/countries/resolve")

    assert response.status_code == 422


def test_resolve_k_out_of_range_returns_422():
    response = client.get("/v1/countries/resolve", params={"q": "alemania", "k": 100})

    assert response.status_code == 422
