"""Vector store using PostgreSQL with pgvector extension."""

import psycopg2

from src.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    embeddings,
)


def get_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def search_countries(query: str, k: int = 10) -> list[dict]:
    """
    Search for similar countries using pgvector cosine similarity.

    Args:
        query: The search query (country name in any language)
        k: Number of results to return

    Returns:
        List of country dictionaries with similarity scores
    """
    query_embedding = embeddings.embed_query(query)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id, name, official_name, iso2, iso3,
            capital, region, subregion, languages, content,
            1 - (embedding <=> %s::vector) as similarity
        FROM countries
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, query_embedding, k),
    )

    columns = [
        "id",
        "name",
        "official_name",
        "iso2",
        "iso3",
        "capital",
        "region",
        "subregion",
        "languages",
        "content",
        "similarity",
    ]

    results = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return results


def search_states(query: str, k: int = 10) -> list[dict]:
    """
    Search for similar states/regions using pgvector cosine similarity.

    Args:
        query: The search query (state name)
        k: Number of results to return

    Returns:
        List of state dictionaries with similarity scores
    """
    query_embedding = embeddings.embed_query(query)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id, original_id, name, country_code, country_name,
            state_code, type, lat, lon, content,
            1 - (embedding <=> %s::vector) as similarity
        FROM states
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, query_embedding, k),
    )

    columns = [
        "id",
        "original_id",
        "name",
        "country_code",
        "country_name",
        "state_code",
        "type",
        "lat",
        "lon",
        "content",
        "similarity",
    ]

    results = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return results


def search_cities(query: str, k: int = 10) -> list[dict]:
    """
    Search for similar cities using pgvector cosine similarity.

    Args:
        query: The search query (city name, partial name, or misspelling)
        k: Number of results to return

    Returns:
        List of city dictionaries with similarity scores
    """
    query_embedding = embeddings.embed_query(query)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id, original_id, name, state_code, state_name,
            country_code, country_name, lat, lon, content,
            1 - (embedding <=> %s::vector) as similarity
        FROM cities
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, query_embedding, k),
    )

    columns = [
        "id",
        "original_id",
        "name",
        "state_code",
        "state_name",
        "country_code",
        "country_name",
        "lat",
        "lon",
        "content",
        "similarity",
    ]

    results = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return results
