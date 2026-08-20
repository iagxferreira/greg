-- Migration: 004_create_resolution_feedback_table
-- Description: Log every country resolution outcome (RAG or Nominatim fallback) as
-- groundwork for a future bandit-style reranker (see ROADMAP.md Phase 4) -- the
-- reranker needs real logged outcomes to train on before it can be built.

CREATE TABLE IF NOT EXISTS resolution_feedback (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('rag', 'nominatim_fallback')),
    matched BOOLEAN NOT NULL,
    result_name VARCHAR(255),
    result_iso2 VARCHAR(10),
    confidence REAL,
    reason TEXT,
    candidates JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Time-ordered exports for training, and per-source breakdown (e.g. how often
-- the Nominatim fallback fires) are the two access patterns expected so far.
CREATE INDEX IF NOT EXISTS resolution_feedback_created_at_idx
ON resolution_feedback (created_at);

CREATE INDEX IF NOT EXISTS resolution_feedback_source_idx
ON resolution_feedback (source);
