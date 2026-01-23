import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
CONTEXT_DIR = PROJECT_ROOT / "context"

# Data files
CITIES_CSV = CONTEXT_DIR / "cities.csv"
STATES_CSV = CONTEXT_DIR / "states.csv"
COUNTRIES_CSV = CONTEXT_DIR / "countries.csv"

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")

# PostgreSQL configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "geo_resolution")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = "mistral:latest"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

# Model configuration
EMBEDDING_DIMENSIONS = 768
LLM_TEMPERATURE = 0

# Vector store configuration
DEFAULT_K_CANDIDATES = 10

# Batch size for embedding operations (no rate limiting needed locally)
EMBEDDING_BATCH_SIZE = 100

# LLM instance
llm = ChatOllama(
    model=OLLAMA_LLM_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=LLM_TEMPERATURE,
)

# Embeddings instance
embeddings = OllamaEmbeddings(
    model=OLLAMA_EMBEDDING_MODEL,
    base_url=OLLAMA_BASE_URL,
)


def validate_config():
    """Validate that required configuration is present."""
    import httpx

    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
    except Exception as e:
        raise ConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
            "Make sure Ollama is running: ollama serve"
        ) from e

    if not CITIES_CSV.exists():
        raise FileNotFoundError(f"Cities data not found: {CITIES_CSV}")
