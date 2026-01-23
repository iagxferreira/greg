-- Migration: 002_create_countries_table
-- Description: Create countries table with vector embeddings for multi-language names

CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    official_name VARCHAR(255),
    tld VARCHAR(255),
    iso2 VARCHAR(255),
    iso3 VARCHAR(255),
    capital VARCHAR(255),
    region VARCHAR(255),
    subregion VARCHAR(255),
    languages TEXT,
    content TEXT,
    embedding vector(768)
);

-- Create HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS countries_embedding_idx
ON countries USING hnsw (embedding vector_cosine_ops);

-- Create index on iso2 for lookups
CREATE INDEX IF NOT EXISTS countries_iso2_idx ON countries (iso2);
