"""Load states data into PostgreSQL with embeddings."""

import csv

from src.config import STATES_CSV
from src.loaders.base import batch_embed, batch_insert


def build_content(row: dict) -> str:
    """Build enriched content string for state embedding."""
    return (
        f"State/Region: {row['name']}\n"
        f"Code: {row['state_code']}\n"
        f"Type: {row.get('type', '')}\n"
        f"Country: {row['country_name']} ({row['country_code']})\n"
        f"Full Reference: {row['name']}, {row['country_name']}"
    )


def load_states():
    """Load states from CSV into PostgreSQL with embeddings."""
    with open(STATES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    print(f"Loading {total} states...")

    # Build all content strings
    print("Building content...")
    contents = [build_content(row) for row in rows]

    # Generate all embeddings in optimized batches
    print("Generating embeddings...")
    all_embeddings = batch_embed(contents)

    # Prepare rows for batch insert
    print("Preparing data...")
    insert_rows = [
        (
            row.get("id"),
            row["name"],
            row.get("country_id"),
            row.get("country_code"),
            row.get("country_name"),
            row.get("state_code"),
            row.get("type"),
            row.get("latitude") or None,
            row.get("longitude") or None,
            content,
            embedding,
        )
        for row, content, embedding in zip(rows, contents, all_embeddings)
    ]

    # Batch insert all rows
    print("Inserting into database...")
    batch_insert(
        table="states",
        columns=[
            "original_id",
            "name",
            "country_id",
            "country_code",
            "country_name",
            "state_code",
            "type",
            "lat",
            "lon",
            "content",
            "embedding",
        ],
        rows=insert_rows,
    )

    print("Done!")


if __name__ == "__main__":
    load_states()
