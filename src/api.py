"""HTTP interface for geo-resolution -- the API counterpart to src/main.py's
CLI. Routes are versioned under /v1/<entity>/resolve so a future
/v1/states/resolve and /v1/cities/resolve (see ROADMAP.md Phase 1 backlog)
slot in the same way once resolve_state/resolve_city exist.

Run locally with: uv run uvicorn src.api:app --reload
"""

from fastapi import FastAPI, HTTPException, Query

from src.models import CountryResult
from src.resolver import resolve_country

app = FastAPI(
    title="Geo-Resolution API",
    description=(
        "Resolves ambiguous, partial, or misspelled country names to structured "
        "geographic data via RAG (pgvector + Ollama), with a Nominatim fallback."
    ),
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check -- does not touch Ollama or Postgres."""
    return {"status": "ok"}


@app.get("/v1/countries/resolve", response_model=CountryResult)
def resolve(
    q: str = Query(..., min_length=1, description="Country name, any language, typos ok"),
    k: int = Query(5, ge=1, le=20, description="Number of RAG candidates to retrieve"),
) -> CountryResult:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="q must not be blank")
    return resolve_country(query, k=k)
