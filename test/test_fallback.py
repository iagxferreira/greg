"""Tests for src.fallback, with httpx mocked out (no real Nominatim calls)."""

from unittest.mock import Mock

import httpx

from src.fallback import FALLBACK_CONFIDENCE, nominatim_country_fallback


def _mock_response(json_data):
    return Mock(raise_for_status=Mock(), json=Mock(return_value=json_data))


def test_returns_country_result_on_success(monkeypatch):
    payload = [
        {
            "display_name": "Deutschland",
            "address": {"country": "Germany", "country_code": "de"},
        }
    ]
    monkeypatch.setattr("src.fallback.httpx.get", Mock(return_value=_mock_response(payload)))

    result = nominatim_country_fallback("alemania")

    assert result is not None
    assert result.matched is True
    assert result.name == "Germany"
    assert result.iso2 == "DE"
    assert result.confidence == FALLBACK_CONFIDENCE


def test_falls_back_to_display_name_when_address_country_missing(monkeypatch):
    payload = [{"display_name": "Germany", "address": {}}]
    monkeypatch.setattr("src.fallback.httpx.get", Mock(return_value=_mock_response(payload)))

    result = nominatim_country_fallback("germany")

    assert result is not None
    assert result.name == "Germany"
    assert result.iso2 is None


def test_returns_none_on_empty_results(monkeypatch):
    monkeypatch.setattr("src.fallback.httpx.get", Mock(return_value=_mock_response([])))

    result = nominatim_country_fallback("asdasdasd")

    assert result is None


def test_returns_none_when_no_usable_name(monkeypatch):
    payload = [{"address": {}}]
    monkeypatch.setattr("src.fallback.httpx.get", Mock(return_value=_mock_response(payload)))

    result = nominatim_country_fallback("asdasdasd")

    assert result is None


def test_returns_none_on_network_error(monkeypatch):
    monkeypatch.setattr(
        "src.fallback.httpx.get", Mock(side_effect=httpx.ConnectError("connection refused"))
    )

    result = nominatim_country_fallback("germany")

    assert result is None


def test_returns_none_on_http_error_status(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "server error", request=Mock(), response=Mock()
    )
    monkeypatch.setattr("src.fallback.httpx.get", Mock(return_value=response))

    result = nominatim_country_fallback("germany")

    assert result is None
