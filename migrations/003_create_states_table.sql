-- Migration: 003_create_states_table
-- Description: Create states table with vector embeddings

CREATE TABLE IF NOT EXISTS states (
    id SERIAL PRIMARY KEY,
    original_id INTEGER,
    name VARCHAR(255) NOT NULL,
    country_id INTEGER,
    country_code VARCHAR(10),
    country_name VARCHAR(255),
    state_code VARCHAR(10),
    type VARCHAR(100),
    lat DECIMAL(10, 6),
    lon DECIMAL(10, 6),
    content TEXT,
    embedding vector(768)
);

-- Create HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS states_embedding_idx
ON states USING hnsw (embedding vector_cosine_ops);

-- Create index on name for text searches
CREATE INDEX IF NOT EXISTS states_name_idx ON states (name);

-- Create index on country_code for filtering
CREATE INDEX IF NOT EXISTS states_country_code_idx ON states (country_code);
