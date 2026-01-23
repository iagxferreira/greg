# Geo-Resolution Engine

A RAG-based system for resolving ambiguous, partial, or misspelled city names to precise geographic coordinates.

## Features

- **Fuzzy matching**: Handles typos and spelling variations ("Pariss" → Paris, France)
- **Disambiguation**: Resolves ambiguous names using global significance ("Paris" → France, not Texas)
- **Context-aware**: Respects explicit hints ("Paris, TX" → Paris, Texas, USA)
- **Structured output**: Returns city, state, country, coordinates, and confidence level

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "GOOGLE_API_KEY=your_key_here" > .env

# Run the resolver
python -m src.main
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
│  Google         │  Convert query to vector
│  Embeddings     │
└────────┬────────┘
         ↓
┌─────────────────┐
│  FAISS Index    │  Similarity search (150K+ cities)
│                 │
└────────┬────────┘
         ↓ top-k candidates
┌─────────────────┐
│  Gemini LLM     │  Disambiguate and select best match
│                 │
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
- Google Cloud API key (for Gemini and Embeddings)

## License

MIT
