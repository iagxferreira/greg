"""Geo-resolution using RAG: vector search + LLM disambiguation."""

import json

from src.config import llm
from src.models import CountryResult
from src.prompt import COUNTRY_RESOLUTION_PROMPT, format_country_candidates
from src.vector_store import search_countries


def resolve_country(user_input: str, k: int = 5) -> CountryResult:
    """
    Resolve a country name using RAG pipeline.

    1. Vector search for top-K candidates
    2. LLM disambiguates and picks the best match
    3. Returns structured CountryResult

    Args:
        user_input: User's country query (any language, misspellings ok)
        k: Number of candidates to retrieve

    Returns:
        CountryResult with matched country or no_match
    """
    # Step 1: Vector search
    candidates = search_countries(user_input, k=k)

    if not candidates:
        return CountryResult.no_match("No candidates found in database")

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
        return CountryResult.from_dict(data)

    except json.JSONDecodeError as e:
        return CountryResult.no_match(f"Failed to parse LLM response: {e}")
    except Exception as e:
        return CountryResult.no_match(f"LLM error: {e}")
