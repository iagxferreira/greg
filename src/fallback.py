"""Nominatim (OpenStreetMap) geocoding fallback for when the RAG pipeline can't
resolve a country with enough confidence — see CONVENTIONS.md for why Nominatim
was chosen over a paid geocoding API."""

import httpx

from src.config import (
    NOMINATIM_BASE_URL,
    NOMINATIM_TIMEOUT_SECONDS,
    NOMINATIM_USER_AGENT,
)
from src.models import CountryResult

# Nominatim doesn't score matches on our 0-1 confidence scale; this fixed value
# reflects "a geocoder found exactly one country-level match" without claiming
# the certainty a strong RAG match would have.
FALLBACK_CONFIDENCE = 0.6


def nominatim_country_fallback(query: str) -> CountryResult | None:
    """
    Look up a country name via Nominatim when the RAG pipeline can't.

    Returns None (rather than raising) on any network error, non-2xx response,
    or empty/unusable result, so callers can fall back to the original RAG
    result without special-casing failures.
    """
    try:
        response = httpx.get(
            f"{NOMINATIM_BASE_URL}/search",
            params={
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "featuretype": "country",
                "limit": 1,
            },
            headers={"User-Agent": NOMINATIM_USER_AGENT},
            timeout=NOMINATIM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    if not results:
        return None

    address = results[0].get("address", {})
    name = address.get("country") or results[0].get("display_name")
    country_code = address.get("country_code")

    if not name:
        return None

    return CountryResult(
        matched=True,
        name=name,
        iso2=country_code.upper() if country_code else None,
        confidence=FALLBACK_CONFIDENCE,
        reason="Resolved via Nominatim fallback — RAG pipeline had no confident match.",
    )
