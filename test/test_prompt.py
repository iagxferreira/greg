"""Tests for src.prompt."""

from src.prompt import format_country_candidates


def test_format_single_candidate_with_content():
    candidates = [
        {
            "name": "Germany",
            "iso2": "DE",
            "official_name": "Federal Republic of Germany",
            "capital": "Berlin",
            "region": "Europe",
            "subregion": "Western Europe",
            "content": "Country: Germany\nAll Names: Germany, Deutschland, Alemania",
        }
    ]

    formatted = format_country_candidates(candidates)

    assert formatted.startswith("1. Germany (DE)")
    assert "Official: Federal Republic of Germany" in formatted
    assert "Names: Germany, Deutschland, Alemania" in formatted


def test_format_candidate_without_content_falls_back_to_name():
    candidates = [
        {
            "name": "Armenia",
            "iso2": "AM",
            "official_name": "Republic of Armenia",
            "capital": "Yerevan",
            "region": "Asia",
            "subregion": "Western Asia",
        }
    ]

    formatted = format_country_candidates(candidates)

    assert "Names: Armenia" in formatted


def test_format_multiple_candidates_are_numbered_and_joined():
    candidates = [
        {
            "name": "Germany",
            "iso2": "DE",
            "official_name": "Federal Republic of Germany",
            "capital": "Berlin",
            "region": "Europe",
            "subregion": "Western Europe",
            "content": "All Names: Germany",
        },
        {
            "name": "Armenia",
            "iso2": "AM",
            "official_name": "Republic of Armenia",
            "capital": "Yerevan",
            "region": "Asia",
            "subregion": "Western Asia",
            "content": "All Names: Armenia",
        },
    ]

    formatted = format_country_candidates(candidates)
    lines = formatted.split("\n")

    assert lines[0].startswith("1. Germany")
    assert any(line.startswith("2. Armenia") for line in lines)
