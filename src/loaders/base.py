"""Base loader with optimized batch operations."""

from psycopg2.extras import execute_values

from src.config import EMBEDDING_BATCH_SIZE, embeddings
from src.vector_store import get_connection

# Insert many rows at once with execute_values
DEFAULT_INSERT_BATCH_SIZE = 1000


def batch_embed(
    texts: list[str], batch_size: int = EMBEDDING_BATCH_SIZE
) -> list[list[float]]:
    """
    Generate embeddings in batches.

    Args:
        texts: List of texts to embed
        batch_size: Number of texts per batch

    Returns:
        List of embeddings
    """
    all_embeddings = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = embeddings.embed_documents(batch)
        all_embeddings.extend(batch_embeddings)

        progress = min(i + batch_size, total)
        print(f"  Embedded {progress}/{total} texts ({progress * 100 // total}%)")

    return all_embeddings


def batch_insert(
    table: str,
    columns: list[str],
    rows: list[tuple],
    batch_size: int = DEFAULT_INSERT_BATCH_SIZE,
):
    """
    Insert rows in optimized batches using execute_values.

    Args:
        table: Table name
        columns: List of column names
        rows: List of tuples with values
        batch_size: Number of rows per INSERT statement
    """
    conn = get_connection()
    cursor = conn.cursor()

    cols = ", ".join(columns)
    total = len(rows)

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]

        execute_values(
            cursor,
            f"INSERT INTO {table} ({cols}) VALUES %s",
            batch,
            template=None,
            page_size=batch_size,
        )

        conn.commit()
        progress = min(i + batch_size, total)
        print(f"  Inserted {progress}/{total} rows ({progress * 100 // total}%)")

    cursor.close()
    conn.close()
