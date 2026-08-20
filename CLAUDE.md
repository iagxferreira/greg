# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Geo-resolution RAG system that takes ambiguous/partial/misspelled location input, retrieves
candidates via pgvector similarity search, and uses an LLM to disambiguate and return structured
geographic data. **Country resolution is fully implemented; city/state resolution is not** — see
Architecture below.

See `ROADMAP.md` for the phased plan this project is following and `CONVENTIONS.md` for the
commit/branch/PR workflow and the tradeoffs behind past decisions — both are living documents,
check them for current status rather than assuming this file alone is up to date.

## Commands

```bash
# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Run the geo-resolver CLI (country resolution only, see Architecture)
uv run python -m src.main "<country query>"

# Lint / format
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest test/

# Run a single test
uv run pytest test/test_resolver.py::test_function_name -v
```

## Environment Setup

Requires a running Ollama server with the `mistral:latest` and `nomic-embed-text` models pulled,
and a PostgreSQL instance with the `pgvector` extension. `docker compose up -d` starts both (see
`docker-compose.yml`: `postgres` auto-applies `migrations/*.sql` on first init, `ollama` + the
one-shot `ollama-init` job pull the required models) — the app itself still runs locally via
`uv run`, only its two dependencies are containerized. Configuration is read from `.env` — see
`.env.example` for `OLLAMA_BASE_URL`, `POSTGRES_*`, and `NOMINATIM_*` vars, all of which have
local-dev defaults in `src/config.py` that match the compose file's defaults.

Before first use (skip the migrations if you used `docker compose up -d`), apply the migrations in
`migrations/` and run the loaders in `src/loaders/` to populate and embed the `countries`,
`states`, and `cities` tables from `context/*.csv`.

## Architecture

### RAG Pipeline Flow (country resolution — the only resolver implemented today)

```
User Input → Ollama embeddings (nomic-embed-text) → pgvector similarity search
    → Top-K candidates → Ollama LLM (mistral:latest) disambiguation → CountryResult
                                        │
                    matched=False or confidence < FALLBACK_CONFIDENCE_THRESHOLD
                                        ▼
                          Nominatim (OpenStreetMap) geocoding fallback
```

If the RAG result is unmatched or below `FALLBACK_CONFIDENCE_THRESHOLD` (`src/config.py`), the
resolver calls `src/fallback.py:nominatim_country_fallback` and returns that instead when it
succeeds; on fallback failure (network error, no result) the original RAG result is returned
unchanged. See `CONVENTIONS.md` for why Nominatim was chosen over a paid geocoding API.

Every call to `resolve_country()` — regardless of which path won — is logged via
`src/feedback.py:log_resolution` to the `resolution_feedback` table (`migrations/004_*.sql`):
query, source (`rag`/`nominatim_fallback`), result, and the raw candidates considered. This is
groundwork for the Phase 4 bandit reranker, not a reranker itself — see `ROADMAP.md`. Logging is
best-effort: a DB failure here is swallowed (warning to stderr) and never breaks resolution.

### Core Modules (src/)

- **config.py**: loads `.env`, builds the shared `llm` (`ChatOllama`) and `embeddings`
  (`OllamaEmbeddings`) instances, validates Ollama connectivity and CSV presence.
- **vector_store.py**: pgvector cosine-similarity search (`search_countries`, `search_states`,
  `search_cities`) against PostgreSQL. States and cities search functions exist but nothing calls
  them yet — see the resolver gap below.
- **prompt.py**: `COUNTRY_RESOLUTION_PROMPT` template + candidate formatting for country
  disambiguation.
- **resolver.py**: `resolve_country()` — RAG pipeline (search → prompt → LLM → parse JSON →
  `CountryResult`) plus the Nominatim fallback trigger. No `resolve_state`/`resolve_city`
  equivalent exists yet.
- **fallback.py**: `nominatim_country_fallback()` — geocodes via the Nominatim `/search` API
  (`featuretype=country`), returns `None` on any failure so the caller can keep the RAG result.
- **feedback.py**: `log_resolution()` — best-effort insert into `resolution_feedback` for every
  resolution outcome; failures are caught and printed to stderr, never raised.
- **models.py**: `CountryResult` dataclass (matched, name, iso2/iso3, capital, region, confidence,
  reason).
- **main.py**: single-shot CLI — `python -m src.main "<query>"` resolves one country and prints
  the result. Not the interactive city-resolution loop the original README implied.
- **loaders/**: `load_countries`, `load_states`, `load_cities` — read `context/*.csv`, build
  enriched embedding text (`base.build_content` per loader), embed in batches via
  `loaders/base.py:batch_embed`, and bulk-insert via `loaders/base.py:batch_insert`.

### Data (context/)

| File | Records | Key Fields |
|------|---------|------------|
| cities.csv | 150K+ | id, name, state_code, state_name, country_code, country_name, lat, lon |
| states.csv | 5K+ | id, name, country_code, state_code, type, lat, lon |
| countries.csv | 250 | ISO codes, translations (20+ languages), capital, region/subregion |

### Storage: PostgreSQL + pgvector (not FAISS)

Each of `cities`, `states`, `countries` (see `migrations/00{1,2,3}_*.sql`) has an `embedding
vector(768)` column with an HNSW cosine-similarity index, plus a `content` column holding the
enriched text that was embedded — not raw CSV fields — for better semantic matching, e.g. for a
city:
```
City: Paris
State/Region: Ile-de-France (IDF)
Country: France (FR)
Full Reference: Paris, Ile-de-France, France
```

There is no local vector index file (no FAISS) — similarity search is a SQL query via `psycopg2`
(`src/vector_store.py`), so PostgreSQL must be reachable to resolve anything.

### Known gap

`states`/`cities` are loaded and searchable but have no resolver, prompt, or CLI wiring — resolving
a city or state name currently isn't possible end-to-end. Tracked as backlog in `ROADMAP.md`.
