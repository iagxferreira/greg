-- Migration: 001_create_cities_table
-- Description: Enable pgvector extension and create cities table with vector embeddings

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create cities table
CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    original_id INTEGER,
    name VARCHAR(255) NOT NULL,
    state_id INTEGER,
    state_code VARCHAR(10),
    state_name VARCHAR(255),
    country_id INTEGER,
    country_code VARCHAR(10),
    country_name VARCHAR(255),
    lat DECIMAL(10, 6),
    lon DECIMAL(10, 6),
    wikidata_id VARCHAR(50),
    content TEXT,
    embedding vector(768)
);

-- Create HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS cities_embedding_idx
ON cities USING hnsw (embedding vector_cosine_ops);

-- Create index on name for text searches
CREATE INDEX IF NOT EXISTS cities_name_idx ON cities (name);

-- Create index on country_code for filtering
CREATE INDEX IF NOT EXISTS cities_country_code_idx ON cities (country_code);
