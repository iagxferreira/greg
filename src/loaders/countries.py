"""Load countries data into PostgreSQL with embeddings."""

import csv

from src.config import COUNTRIES_CSV, EMBEDDING_BATCH_SIZE, embeddings
from src.vector_store import get_connection


def build_content(row: list) -> str:
    """Build enriched content string for country embedding."""
    name = row[0]
    official_name = row[1]
    iso2 = row[3]
    iso3 = row[5]
    capital = row[13]
    region = row[15]
    subregion = row[16]
    languages = row[17]

    translations = set()
    translations.add(name)
    translations.add(official_name)
    for i in range(18, min(58, len(row))):
        if row[i] and row[i].strip():
            translations.add(row[i].strip())
    translations.discard("")

    return (
        f"Country: {name}\n"
        f"Official Name: {official_name}\n"
        f"ISO Codes: {iso2}, {iso3}\n"
        f"Capital: {capital}\n"
        f"Region: {region}, {subregion}\n"
        f"Languages: {languages}\n"
        f"All Names: {', '.join(translations)}"
    )


def build_row(row: list, content: str, embedding: list) -> tuple:
    """Build insert row tuple."""
    return (
        row[0],  # name
        row[1],  # official_name
        row[2],  # tld
        row[3],  # iso2
        row[5],  # iso3
        row[13],  # capital
        row[15],  # region
        row[16],  # subregion
        row[17],  # languages
        content,
        embedding,
    )


def load_countries():
    """Load countries from CSV into PostgreSQL with embeddings."""
    with open(COUNTRIES_CSV, encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    total = len(rows)
    print(f"Loading {total} countries...")

    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM countries")
    conn.commit()

    columns = [
        "name",
        "official_name",
        "tld",
        "iso2",
        "iso3",
        "capital",
        "region",
        "subregion",
        "languages",
        "content",
        "embedding",
    ]
    cols_str = ", ".join(columns)

    for i in range(0, total, EMBEDDING_BATCH_SIZE):
        batch_rows = rows[i : i + EMBEDDING_BATCH_SIZE]
        batch_contents = [build_content(row) for row in batch_rows]

        batch_embeddings = embeddings.embed_documents(batch_contents)

        insert_rows = [
            build_row(row, content, emb)
            for row, content, emb in zip(batch_rows, batch_contents, batch_embeddings, strict=True)
        ]

        for insert_row in insert_rows:
            cursor.execute(
                f"INSERT INTO countries ({cols_str}) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)",
                insert_row,
            )

        conn.commit()

        progress = min(i + EMBEDDING_BATCH_SIZE, total)
        print(f"  Processed {progress}/{total} countries ({progress * 100 // total}%)")

    cursor.close()
    conn.close()
    print("Done!")


if __name__ == "__main__":
    load_countries()
