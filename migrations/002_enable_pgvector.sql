-- 002_enable_pgvector.sql
-- Enables vector search for the knowledge base. Keep the local TF-IDF/LSA index
-- as a fallback for offline resilience.

-- Enable the extension once per project.
CREATE EXTENSION IF NOT EXISTS vector;

-- Chunked knowledge documents with 384-dimensional embeddings
-- (matches sentence-transformers/all-MiniLM-L6-v2).
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id text NOT NULL,
    chunk_text text NOT NULL,
    embedding vector(384),
    source text,
    space text,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz DEFAULT now()
);

-- Approximate nearest-neighbor index for cosine similarity.
-- Lists tuned for roughly 1k-100k chunks; re-run ANALYZE after bulk loads.
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
    ON knowledge_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc_id
    ON knowledge_chunks (doc_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_space
    ON knowledge_chunks (space);

-- Helper function: semantic search returning top-k results with cosine distance.
CREATE OR REPLACE FUNCTION match_knowledge_chunks(
    query_embedding vector(384),
    match_threshold float,
    match_count int,
    filter_space text DEFAULT NULL
)
RETURNS TABLE(
    id uuid,
    doc_id text,
    chunk_text text,
    source text,
    space text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kc.id,
        kc.doc_id,
        kc.chunk_text,
        kc.source,
        kc.space,
        1 - (kc.embedding <=> query_embedding) AS similarity
    FROM knowledge_chunks kc
    WHERE
        (filter_space IS NULL OR kc.space = filter_space)
        AND 1 - (kc.embedding <=> query_embedding) > match_threshold
    ORDER BY kc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
