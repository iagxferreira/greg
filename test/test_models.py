"""Tests for src.models."""

from src.models import CountryResult


def test_from_dict_full():
    data = {
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

    result = CountryResult.from_dict(data)

    assert result.matched is True
    assert result.name == "Germany"
    assert result.iso2 == "DE"
    assert result.iso3 == "DEU"
    assert result.confidence == 0.95
    assert result.reason == data["reason"]


def test_from_dict_missing_fields_uses_defaults():
    result = CountryResult.from_dict({})

    assert result.matched is False
    assert result.name is None
    assert result.confidence == 0.0
    assert result.reason == ""


def test_no_match_default_reason():
    result = CountryResult.no_match()

    assert result.matched is False
    assert result.confidence == 0.0
    assert result.reason == "No matching country found"


def test_no_match_custom_reason():
    result = CountryResult.no_match("No candidates found in database")

    assert result.matched is False
    assert result.reason == "No candidates found in database"
