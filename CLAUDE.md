# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Geo-resolution RAG system that takes ambiguous/partial/misspelled city input, retrieves candidates via FAISS vector similarity search, and uses an LLM to disambiguate and return structured location data with coordinates.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the geo-resolver CLI
python -m src.main

# Run tests
pytest test/

# Run a single test
pytest test/test_resolver.py::test_function_name -v
```

## Environment Setup

Requires `GOOGLE_API_KEY` in `.env` file for Google Generative AI (Gemini LLM and embeddings).

## Architecture

### RAG Pipeline Flow

```
User Input → Embeddings → FAISS Search → Top-K Candidates → LLM Disambiguation → GeoResult
```

### Core Modules (src/)

- **embeddings.py**: Google Generative AI embeddings (`models/embedding-001`)
- **llm.py**: Gemini LLM (`gemini-1.5-pro`, temperature=0)
- **vector_store.py**: FAISS index built from cities.csv with enriched documents
- **prompt.py**: Geo-resolution prompt template for LLM disambiguation
- **main.py**: `GeoResolver` class orchestrating the pipeline + CLI interface

### Data (context/)

| File | Records | Key Fields |
|------|---------|------------|
| cities.csv | 150K+ | id, name, state_code, state_name, country_code, country_name, lat, lon |
| states.csv | 5K+ | id, name, country_code, state_code, type, lat, lon |
| countries.csv | 250 | ISO codes, translations (20+ languages), currency, timezone |

### Vector Store Strategy

Cities are indexed as enriched documents (not raw CSV rows) for better semantic matching:
```
City: Paris
State/Region: Ile-de-France (IDF)
Country: France (FR)
Full Reference: Paris, Ile-de-France, France
```

FAISS index persists to `faiss_index/` after first build.
