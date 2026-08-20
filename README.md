# Geo-Resolution Engine

A RAG-based system for resolving ambiguous, partial, or misspelled city names to precise geographic coordinates.

## Features

- **Fuzzy matching**: Handles typos and spelling variations ("Pariss" → Paris, France)
- **Disambiguation**: Resolves ambiguous names using global significance ("Paris" → France, not Texas)
- **Context-aware**: Respects explicit hints ("Paris, TX" → Paris, Texas, USA)
- **Structured output**: Returns city, state, country, coordinates, and confidence level

## Prerequisites

### Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com/) or via command line:

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS (via Homebrew)
brew install ollama
```

### Pull Required Models

This application requires two Ollama models:

```bash
# Pull the Mistral LLM (for disambiguation)
ollama pull mistral:latest

# Pull the Nomic embedding model (for vector search)
ollama pull nomic-embed-text
```

### Start Ollama Server

Make sure Ollama is running before starting the application:

```bash
ollama serve
```

### PostgreSQL with pgvector

The application uses PostgreSQL with the pgvector extension for vector storage:

```bash
# Install pgvector extension (Ubuntu/Debian)
sudo apt install postgresql-16-pgvector

# Or via Docker
docker run -d --name pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=geo_resolution \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

## Quick Start

```bash
# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Set up environment (optional - defaults work for local setup)
cp .env.example .env
```

### Database Setup

Run migrations to create the required tables:

```bash
psql -h localhost -U postgres -d geo_resolution -f migrations/001_create_cities_table.sql
psql -h localhost -U postgres -d geo_resolution -f migrations/002_create_countries_table.sql
psql -h localhost -U postgres -d geo_resolution -f migrations/003_create_states_table.sql
psql -h localhost -U postgres -d geo_resolution -f migrations/004_create_resolution_feedback_table.sql
```

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
```

## Usage

```
Geo-Resolution Engine
==================================================
Enter a city name (partial, misspelled, or ambiguous)
Type 'quit' to exit

Location> NYC

  Resolved: New York City, New York, United States
  Coordinates: 40.7128, -74.0060
  Confidence: high
  Reasoning: NYC is the common abbreviation for New York City
```

## Example Resolutions

| Input | Output | Reasoning |
|-------|--------|-----------|
| `Paris` | Paris, France | Most globally significant |
| `Paris, TX` | Paris, Texas, USA | Explicit state context |
| `Pariss` | Paris, France | Typo correction |
| `NYC` | New York City, NY, USA | Common abbreviation |
| `springfield il` | Springfield, IL, USA | State context provided |

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
│  pgvector       │  (150K+ cities indexed)
└────────┬────────┘
         ↓ top-k candidates
┌─────────────────┐
│  Ollama         │  Disambiguate and select best match
│  Mistral LLM    │  (mistral:latest model)
└────────┬────────┘
         ↓
┌─────────────────┐
│  GeoResult      │  {city, state, country, lat, lon, confidence}
└─────────────────┘
```

## Data Sources

- **cities.csv**: 150,000+ cities with coordinates
- **states.csv**: 5,000+ states/provinces
- **countries.csv**: 250 countries with multilingual names

## Requirements

- Python 3.10+
- Ollama with `mistral:latest` and `nomic-embed-text` models
- PostgreSQL 14+ with pgvector extension

## License

MIT
