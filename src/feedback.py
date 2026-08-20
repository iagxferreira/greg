"""Logs every country resolution outcome to `resolution_feedback` — groundwork
for the bandit-style reranker in ROADMAP.md Phase 4. See CONVENTIONS.md for
why logging has to land and accumulate data before that reranker is buildable."""

import json
import sys

from src.models import CountryResult
from src.vector_store import get_connection


def log_resolution(query: str, source: str, result: CountryResult, candidates: list[dict]) -> None:
    """
    Record one resolution outcome.

    Args:
        query: the raw user input
        source: "rag" or "nominatim_fallback" — which path produced `result`
        result: the CountryResult returned to the caller
        candidates: the raw pgvector search results considered (empty if the
            fallback fired because there were no candidates at all)

    Best-effort: a logging failure is printed to stderr and swallowed so a
    broken feedback pipeline never breaks resolution itself.
    """
    candidate_summaries = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "iso2": c.get("iso2"),
            "similarity": c.get("similarity"),
        }
        for c in candidates
    ]

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO resolution_feedback
                (query, source, matched, result_name, result_iso2, confidence, reason, candidates)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                query,
                source,
                result.matched,
                result.name,
                result.iso2,
                result.confidence,
                result.reason,
                json.dumps(candidate_summaries),
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Warning: failed to log resolution feedback: {e}", file=sys.stderr)
