# Geo-Resolution Engine

A RAG-based system for resolving ambiguous, partial, or misspelled location names to structured
geographic data. **Country resolution is fully implemented today; city/state resolution is a
backlog item** — see [ROADMAP.md](ROADMAP.md) for what's built vs planned, and
[CONVENTIONS.md](CONVENTIONS.md) for the tradeoffs behind how it's built.

## Features

- **Fuzzy matching**: Handles typos and spelling variations ("Jermany" → Germany)
- **Multilingual**: Recognizes translations and aliases ("alemania" → Germany, "japon" → Japan)
- **Disambiguation**: An LLM picks the best match from pgvector-retrieved candidates, not a naive
  nearest-neighbor lookup
- **Resilient**: Falls back to Nominatim (OpenStreetMap) geocoding when the RAG pipeline has no
  confident match, instead of failing outright
- **Structured output**: Returns name, ISO codes, capital, region/subregion, confidence, and the
  reasoning behind the match

## Prerequisites

The app itself runs locally (`uv run ...`); it needs Ollama and PostgreSQL/pgvector reachable.
Pick one:

### Option A: Docker (recommended)

```bash
docker compose up -d
```

This starts `postgres` (pgvector, with `migrations/*.sql` auto-applied on first init — see the
Database Setup note below) and `ollama`, then a one-shot `ollama-init` job pulls `mistral:latest`
and `nomic-embed-text` into a persisted volume. First run takes a few minutes for the model pulls;
`docker compose ps` shows when `ollama-init` has exited (status `0`). Re-running `docker compose up`
later is cheap — `ollama pull` no-ops once a model is cached.

Uses the public ports `11434` (Ollama) and `5432` (Postgres, override with `POSTGRES_PORT`), so the
defaults in `.env.example` work unchanged.

### Option B: Native install

<details>
<summary>Install Ollama, pull models, and set up PostgreSQL/pgvector by hand</summary>

**Install Ollama** from [ollama.com](https://ollama.com/) or via command line:

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS (via Homebrew)
brew install ollama
```

**Pull the required models:**

```bash
ollama pull mistral:latest
ollama pull nomic-embed-text
```

**Start the Ollama server:**

```bash
ollama serve
```

**Install PostgreSQL with pgvector:**

```bash
# Ubuntu/Debian
sudo apt install postgresql-16-pgvector

# Or run just the Postgres container from docker-compose.yml:
docker compose up -d postgres
```

</details>

## Quick Start

```bash
# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Set up environment (optional - defaults work for local setup)
cp .env.example .env
```

### Database Setup

**If you used `docker compose up -d`, the tables already exist** — Postgres auto-runs everything
in `migrations/` on first init of an empty data volume. Otherwise, apply them by hand:

```bash
psql -h localhost -U postgres -d geo_resolution -f migrations/001_create_cities_table.sql
psql -h localhost -U postgres -d geo_resolution -f migrations/002_create_countries_table.sql
psql -h localhost -U postgres -d geo_resolution -f migrations/003_create_states_table.sql
psql -h localhost -U postgres -d geo_resolution -f migrations/004_create_resolution_feedback_table.sql
```

(This also applies if you're reusing an existing `postgres_data` volume from before this table was
added — auto-init only runs against an empty volume, so run the migration manually in that case.)

### Data Indexing

Before using the application, you must index the geographic data. This step generates vector embeddings for all locations using the `nomic-embed-text` model and stores them in PostgreSQL:

```bash
# Index countries (~250 records)
uv run python -m src.loaders.countries

# Index states/provinces (~5K records)
uv run python -m src.loaders.states

# Index cities (~150K records - this may take a while)
uv run python -m src.loaders.cities
```

> **Note**: The indexing process embeds all geographic data using the Ollama embedding model. The cities indexing may take significant time depending on your hardware.

### Run the Application

```bash
uv run python -m src.main
```

## Environment Variables

Create a `.env` file with the following (all have sensible defaults):

```bash
# Ollama (defaults to localhost)
OLLAMA_BASE_URL=http://localhost:11434

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=geo_resolution
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Nominatim geocoding fallback (used when the RAG pipeline has no confident match)
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
NOMINATIM_USER_AGENT=geo-resolution-rag/0.1
```

## Usage

`src/main.py` is a single-shot CLI: pass a country query as an argument, get one resolution back.

```bash
uv run python -m src.main "alemania"
```

```
Resolving: 'alemania'
--------------------------------------------------
Time: 1.34s
--------------------------------------------------
Match: Germany (DE)
Official: Federal Republic of Germany
Capital: Berlin
Region: Europe, Western Europe
Confidence: 95%
Reason: Alemania is the Spanish translation for Germany
```

## Example Resolutions

| Input | Output | Reasoning |
|-------|--------|-----------|
| `alemania` | Germany | Spanish translation, resolved via RAG |
| `japon` | Japan | French translation, resolved via RAG |
| `Jermany` | Germany | Typo correction, resolved via RAG |
| `brasil` | Brazil | Portuguese spelling, resolved via RAG |
| a query the RAG pipeline can't confidently place | best-effort match | Nominatim fallback |

## Architecture

```
User Input
    ↓
┌─────────────────┐
│  Ollama         │  Convert query to vector
│  nomic-embed    │  (nomic-embed-text model)
└────────┬────────┘
         ↓
┌─────────────────┐
│  PostgreSQL     │  pgvector similarity search
│  pgvector       │  (250 countries indexed)
└────────┬────────┘
         ↓ top-k candidates
┌─────────────────┐
│  Ollama         │  Disambiguate and select best match
│  Mistral LLM    │  (mistral:latest model)
└────────┬────────┘
         ↓
   matched=False or low confidence?
         ↓ yes                    ↓ no
┌─────────────────┐               │
│  Nominatim      │               │
│  fallback       │               │
└────────┬────────┘               │
         ↓                        ↓
┌───────────────────────────────────────┐
│  CountryResult                        │  {name, iso2/iso3, capital,
│  (also logged to resolution_feedback) │   region, confidence, reason}
└───────────────────────────────────────┘
```

See [CLAUDE.md](CLAUDE.md) for the module-by-module breakdown (`src/resolver.py`,
`src/fallback.py`, `src/feedback.py`, etc.).

## Data Sources

- **countries.csv**: 250 countries with multilingual names — the only one actively resolved today.
- **cities.csv**: 150,000+ cities with coordinates — loaded and embedded, but not yet resolvable
  end-to-end (see [ROADMAP.md](ROADMAP.md)).
- **states.csv**: 5,000+ states/provinces — same status as cities.

## Requirements

- Python 3.10+
- Ollama with `mistral:latest` and `nomic-embed-text` models
- PostgreSQL 14+ with pgvector extension

## License

MIT
