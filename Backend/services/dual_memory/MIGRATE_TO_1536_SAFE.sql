-- ============================================================================
-- Safe Migration: 768 → 1536 Dimensions (Clears Old Data)
-- ============================================================================
-- This migration handles existing 768-dimensional embeddings by clearing them
-- ============================================================================

-- CRITICAL: This will DELETE all existing embeddings!
-- They will be regenerated as users interact with the system.
-- Make sure you have a backup before running this!

-- ============================================================================
-- STEP 1: CLEAR OLD EMBEDDINGS
-- ============================================================================

-- Option A: Set embeddings to NULL (preserves rows)
UPDATE user_conversational_memory SET embedding = NULL;
UPDATE document_chunks SET embedding = NULL;
UPDATE user_business_facts SET embedding = NULL;
UPDATE user_risks SET embedding = NULL WHERE embedding IS NOT NULL;
UPDATE document_notes SET note_embedding = NULL WHERE note_embedding IS NOT NULL;

-- Option B: Delete all rows with embeddings (if you want fresh start)
-- UNCOMMENT if you prefer to delete everything:
-- DELETE FROM user_conversational_memory;
-- DELETE FROM document_chunks;
-- DELETE FROM user_business_facts;
-- DELETE FROM user_risks WHERE embedding IS NOT NULL;
-- DELETE FROM document_notes WHERE note_embedding IS NOT NULL;

-- ============================================================================
-- STEP 2: DROP INDEXES
-- ============================================================================

DROP INDEX IF EXISTS user_conversational_memory_embedding_idx;
DROP INDEX IF EXISTS document_chunks_embedding_idx;
DROP INDEX IF EXISTS user_business_facts_embedding_idx;
DROP INDEX IF EXISTS user_risks_embedding_idx;
DROP INDEX IF EXISTS document_notes_embedding_idx;
DROP INDEX IF EXISTS super_notes_embedding_idx;

-- ============================================================================
-- STEP 3: ALTER COLUMN TYPES
-- ============================================================================

-- Update column type for user_conversational_memory
ALTER TABLE user_conversational_memory
ALTER COLUMN embedding TYPE vector(1536);

-- Update column type for document_chunks
ALTER TABLE document_chunks
ALTER COLUMN embedding TYPE vector(1536);

-- Update column type for user_business_facts
ALTER TABLE user_business_facts
ALTER COLUMN embedding TYPE vector(1536);

-- Update column type for user_risks
ALTER TABLE user_risks
ALTER COLUMN embedding TYPE vector(1536);

-- Update column type for document_notes
ALTER TABLE document_notes
ALTER COLUMN note_embedding TYPE vector(1536);

-- Update column type for super_notes (if exists)
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
    END IF;
END $$;

-- ============================================================================
-- STEP 4: RECREATE INDEXES
-- ============================================================================

-- user_conversational_memory
CREATE INDEX user_conversational_memory_embedding_idx
ON user_conversational_memory
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- document_chunks
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- user_business_facts
CREATE INDEX user_business_facts_embedding_idx
ON user_business_facts
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- user_risks
CREATE INDEX user_risks_embedding_idx
ON user_risks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- document_notes
CREATE INDEX document_notes_embedding_idx
ON document_notes
USING hnsw (note_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- super_notes (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'super_notes'
        AND column_name = 'embedding'
    ) THEN
        CREATE INDEX IF NOT EXISTS super_notes_embedding_idx
        ON super_notes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    END IF;
END $$;

-- ============================================================================
-- STEP 5: UPDATE RPC FUNCTIONS
-- ============================================================================

-- Drop existing functions first (parameter types are changing)
DROP FUNCTION IF EXISTS match_user_conversations(vector, integer, uuid, text);
DROP FUNCTION IF EXISTS match_user_facts(vector, integer, uuid);
DROP FUNCTION IF EXISTS match_user_facts_v15(vector, integer, uuid, float);
DROP FUNCTION IF EXISTS match_document_chunks(vector, float, integer, uuid);

-- match_user_conversations
CREATE OR REPLACE FUNCTION match_user_conversations(
    query_embedding vector(1536),
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
        AND user_conversational_memory.embedding IS NOT NULL
        AND (p_session_id IS NULL OR user_conversational_memory.session_id = p_session_id)
    ORDER BY user_conversational_memory.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- match_user_facts
CREATE OR REPLACE FUNCTION match_user_facts(
    query_embedding vector(1536),
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
        AND user_business_facts.embedding IS NOT NULL
    ORDER BY user_business_facts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- match_user_facts_v15
CREATE OR REPLACE FUNCTION match_user_facts_v15(
    query_embedding vector(1536),
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
        AND user_business_facts.embedding IS NOT NULL
        AND user_business_facts.valid_to IS NULL
        AND user_business_facts.verification_status NOT IN ('DEPRECATED', 'CONTESTED')
        AND user_business_facts.confidence_score >= min_confidence
    ORDER BY user_business_facts.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- match_document_chunks
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(1536),
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
        AND document_chunks.embedding IS NOT NULL
        AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check column types
SELECT
    table_name,
    column_name,
    udt_name
FROM information_schema.columns
WHERE column_name LIKE '%embedding%'
    AND table_schema = 'public'
ORDER BY table_name, column_name;

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname LIKE '%embedding%'
    AND schemaname = 'public'
ORDER BY tablename;

-- Count NULL embeddings (should show all if you used Option A)
SELECT
    'user_conversational_memory' as table_name,
    COUNT(*) as total_rows,
    COUNT(embedding) as rows_with_embedding,
    COUNT(*) - COUNT(embedding) as rows_null_embedding
FROM user_conversational_memory
UNION ALL
SELECT
    'document_chunks',
    COUNT(*),
    COUNT(embedding),
    COUNT(*) - COUNT(embedding)
FROM document_chunks
UNION ALL
SELECT
    'user_business_facts',
    COUNT(*),
    COUNT(embedding),
    COUNT(*) - COUNT(embedding)
FROM user_business_facts;

-- ============================================================================
-- COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Embeddings will be regenerated as:
--    - Users chat (conversational memory)
--    - Documents are uploaded (document chunks)
--    - Facts are extracted (business facts)
-- 2. V1.5 TMS will handle deduplication automatically
-- 3. Test with: python Backend/Agents/test_agent_with_v15_memory.py
-- ============================================================================
