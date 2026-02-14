-- ============================================================================
-- Update Embedding Dimensions from 768 to 1536
-- ============================================================================
-- Gemini embedding-001 uses Matryoshka Representation Learning (MRL)
-- Default: 3072 dims, but configurable to 768, 1536, or 3072
-- We use 1536 for optimal balance:
--   - Better quality than 768
--   - Fits within IVFFlat 2000-dim limit
--   - Saves storage vs 3072
--   - Google-recommended size
-- ============================================================================

-- CRITICAL: This will drop and recreate vector indexes
-- Make sure you have a backup before running this!

-- NOTE: Can use IVFFlat (faster) since 1536 < 2000 dimension limit
-- If you prefer HNSW for better recall, change index type below

-- ============================================================================
-- 1. UPDATE user_conversational_memory TABLE
-- ============================================================================

-- Drop existing vector index (if exists)
DROP INDEX IF EXISTS user_conversational_memory_embedding_idx;

-- Update column type
ALTER TABLE user_conversational_memory
ALTER COLUMN embedding TYPE vector(1536);

-- Recreate vector index for fast similarity search
-- Note: Using HNSW instead of IVFFlat (IVFFlat limited to 2000 dimensions)
CREATE INDEX user_conversational_memory_embedding_idx
ON user_conversational_memory
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 2. UPDATE document_chunks TABLE
-- ============================================================================

-- Drop existing vector index (if exists)
DROP INDEX IF EXISTS document_chunks_embedding_idx;

-- Update column type
ALTER TABLE document_chunks
ALTER COLUMN embedding TYPE vector(1536);

-- Recreate vector index
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 3. UPDATE user_business_facts TABLE
-- ============================================================================

-- Drop existing vector index (if exists)
DROP INDEX IF EXISTS user_business_facts_embedding_idx;

-- Update column type
ALTER TABLE user_business_facts
ALTER COLUMN embedding TYPE vector(1536);

-- Recreate vector index
CREATE INDEX user_business_facts_embedding_idx
ON user_business_facts
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 4. UPDATE user_risks TABLE
-- ============================================================================

-- Drop existing vector index (if exists)
DROP INDEX IF EXISTS user_risks_embedding_idx;

-- Update column type (if column exists)
ALTER TABLE user_risks
ALTER COLUMN embedding TYPE vector(1536);

-- Recreate vector index
CREATE INDEX user_risks_embedding_idx
ON user_risks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 5. UPDATE document_notes TABLE (if it has embeddings)
-- ============================================================================

-- Drop existing vector index (if exists)
DROP INDEX IF EXISTS document_notes_embedding_idx;

-- Update column type (note_embedding)
ALTER TABLE document_notes
ALTER COLUMN note_embedding TYPE vector(1536);

-- Recreate vector index
CREATE INDEX document_notes_embedding_idx
ON document_notes
USING hnsw (note_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 6. UPDATE super_notes TABLE (if it has embeddings)
-- ============================================================================

-- Drop existing vector index (if exists)
DROP INDEX IF EXISTS super_notes_embedding_idx;

-- Update column type (if column exists)
-- Check if super_notes has an embedding column first
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'super_notes'
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE super_notes
        ALTER COLUMN embedding TYPE vector(1536);

        CREATE INDEX IF NOT EXISTS super_notes_embedding_idx
        ON super_notes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    END IF;
END $$;

-- ============================================================================
-- 7. UPDATE RPC FUNCTIONS
-- ============================================================================

-- Update match_user_conversations function
CREATE OR REPLACE FUNCTION match_user_conversations(
    query_embedding vector(1536),  -- ← Updated from 768
    match_count int,
    p_user_id uuid,
    p_session_id text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    session_id text,
    query text,
    response_summary text,
    entities jsonb,
    created_at timestamptz,
    score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        user_conversational_memory.id,
        user_conversational_memory.session_id,
        user_conversational_memory.query,
        user_conversational_memory.response_summary,
        user_conversational_memory.entities,
        user_conversational_memory.created_at,
        1 - (user_conversational_memory.embedding <=> query_embedding) AS score
    FROM user_conversational_memory
    WHERE user_conversational_memory.user_id = p_user_id
        AND (p_session_id IS NULL OR user_conversational_memory.session_id = p_session_id)
    ORDER BY user_conversational_memory.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Update match_user_facts function
CREATE OR REPLACE FUNCTION match_user_facts(
    query_embedding vector(1536),  -- ← Updated from 768
    match_count int,
    p_user_id uuid
)
RETURNS TABLE (
    id uuid,
    subject text,
    predicate text,
    value text,
    fact_type text,
    temporal_context text,
    score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        user_business_facts.id,
        user_business_facts.subject,
        user_business_facts.predicate,
        user_business_facts.value,
        user_business_facts.fact_type,
        user_business_facts.temporal_context,
        1 - (user_business_facts.embedding <=> query_embedding) AS score
    FROM user_business_facts
    WHERE user_business_facts.user_id = p_user_id
    ORDER BY user_business_facts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Update match_user_facts_v15 function (with min_confidence filter)
CREATE OR REPLACE FUNCTION match_user_facts_v15(
    query_embedding vector(1536),  -- ← Updated from 768
    match_count int,
    p_user_id uuid,
    min_confidence float DEFAULT 0.5
)
RETURNS TABLE (
    id uuid,
    subject text,
    predicate text,
    value text,
    fact_type text,
    temporal_context text,
    confidence_score float,
    source_authority text,
    verification_status text,
    score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        user_business_facts.id,
        user_business_facts.subject,
        user_business_facts.predicate,
        user_business_facts.value,
        user_business_facts.fact_type,
        user_business_facts.temporal_context,
        user_business_facts.confidence_score,
        user_business_facts.source_authority,
        user_business_facts.verification_status,
        1 - (user_business_facts.embedding <=> query_embedding) AS score
    FROM user_business_facts
    WHERE user_business_facts.user_id = p_user_id
        AND user_business_facts.valid_to IS NULL  -- Active facts only
        AND user_business_facts.verification_status NOT IN ('DEPRECATED', 'CONTESTED')  -- Verified facts only
        AND user_business_facts.confidence_score >= min_confidence  -- Confidence filter
    ORDER BY user_business_facts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Update match_document_chunks function
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(1536),  -- ← Updated from 768
    match_threshold float,
    match_count int,
    p_user_id uuid
)
RETURNS TABLE (
    id uuid,
    file_path text,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.file_path,
        document_chunks.content,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE document_chunks.user_id = p_user_id
        AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check that all embedding columns are now 3072 dimensions
SELECT
    table_name,
    column_name,
    udt_name,
    (SELECT typlen FROM pg_type WHERE typname = udt_name) as type_length
FROM information_schema.columns
WHERE column_name LIKE '%embedding%'
    AND table_schema = 'public'
ORDER BY table_name, column_name;

-- Expected output: All embedding columns should show vector type

-- Check indexes exist
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname LIKE '%embedding%'
    AND schemaname = 'public'
ORDER BY tablename;

-- ============================================================================
-- NOTES
-- ============================================================================
-- After running this migration:
-- 1. All existing embeddings in the database will be INVALID (768 dims in 3072 slots)
-- 2. You'll need to regenerate embeddings for existing data
-- 3. Or accept that old data won't match new queries (graceful degradation)
-- 4. Going forward, all new embeddings will be 3072 dimensions
-- ============================================================================
