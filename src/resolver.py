"""Geo-resolution using RAG: vector search + LLM disambiguation, with a
Nominatim fallback for low-confidence or no-match results. Every resolution
is logged via src/feedback.py as groundwork for a future reranker."""

import json

from src.config import FALLBACK_CONFIDENCE_THRESHOLD, llm
from src.fallback import nominatim_country_fallback
from src.feedback import log_resolution
from src.models import CountryResult
from src.prompt import COUNTRY_RESOLUTION_PROMPT, format_country_candidates
from src.vector_store import search_countries


def resolve_country(user_input: str, k: int = 5) -> CountryResult:
    """
    Resolve a country name, using RAG first and falling back to Nominatim
    geocoding when the RAG pipeline has no match or a low-confidence one.
    Logs the outcome (source, result, candidates considered) regardless of
    which path wins.

    Args:
        user_input: User's country query (any language, misspellings ok)
        k: Number of candidates to retrieve

    Returns:
        CountryResult with matched country or no_match
    """
    result, candidates = _resolve_country_rag(user_input, k=k)
    source = "rag"

    if not (result.matched and result.confidence >= FALLBACK_CONFIDENCE_THRESHOLD):
        fallback_result = nominatim_country_fallback(user_input)
        if fallback_result is not None:
            result = fallback_result
            source = "nominatim_fallback"

    log_resolution(user_input, source, result, candidates)
    return result


def _resolve_country_rag(user_input: str, k: int) -> tuple[CountryResult, list[dict]]:
    """
    Resolve a country name using the RAG pipeline alone.

    1. Vector search for top-K candidates
    2. LLM disambiguates and picks the best match
    3. Returns the CountryResult plus the raw candidates considered, so the
       caller can log what the search surfaced.
    """
    # Step 1: Vector search
    candidates = search_countries(user_input, k=k)

    if not candidates:
        return CountryResult.no_match("No candidates found in database"), candidates

    # Step 2: Format prompt
    candidates_text = format_country_candidates(candidates)
    prompt = COUNTRY_RESOLUTION_PROMPT.format(
        user_input=user_input,
        candidates=candidates_text,
    )

    # Step 3: LLM disambiguation
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Clean markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        # Parse JSON
        data = json.loads(content)
        return CountryResult.from_dict(data), candidates

    except json.JSONDecodeError as e:
        return CountryResult.no_match(f"Failed to parse LLM response: {e}"), candidates
    except Exception as e:
        return CountryResult.no_match(f"LLM error: {e}"), candidates
