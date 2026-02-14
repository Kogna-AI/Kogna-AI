-- ============================================================================
-- KOGNA 1.5 SCHEMA UPGRADE: Add Epistemic Metadata & Truth Maintenance
-- ============================================================================
-- Run this in Supabase SQL Editor to upgrade from Kogna 1.0 to 1.5
--
-- Changes:
-- 1. Add source_authority, confidence_score, verification_status to fact tables
-- 2. Add valid_to for temporal validity tracking
-- 3. Create sql_memory table for procedural memory (CBR for Text-to-SQL)
-- 4. Create fact_conflicts table for tracking contested facts
-- ============================================================================

-- ============================================================================
-- 1. UPGRADE user_business_facts TABLE
-- ============================================================================

-- Add epistemic metadata columns
ALTER TABLE user_business_facts
ADD COLUMN IF NOT EXISTS source_authority TEXT CHECK (source_authority IN ('ERP', 'PDF', 'CHAT', 'USER_UPLOAD', 'API', 'UNKNOWN')),
ADD COLUMN IF NOT EXISTS confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
ADD COLUMN IF NOT EXISTS verification_status TEXT CHECK (verification_status IN ('VERIFIED', 'PROVISIONAL', 'CONTESTED', 'DEPRECATED')),
ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ;

-- Set defaults for existing rows
UPDATE user_business_facts
SET
    source_authority = 'UNKNOWN',
    confidence_score = 0.7,
    verification_status = 'PROVISIONAL',
    valid_to = NULL,
    last_verified_at = valid_from
WHERE source_authority IS NULL;

-- Create index for faster verification queries
CREATE INDEX IF NOT EXISTS idx_business_facts_verification
ON user_business_facts(user_id, subject, verification_status, valid_to);

-- ============================================================================
-- 2. UPGRADE user_risks TABLE
-- ============================================================================

ALTER TABLE user_risks
ADD COLUMN IF NOT EXISTS source_authority TEXT CHECK (source_authority IN ('ERP', 'PDF', 'CHAT', 'USER_UPLOAD', 'API', 'UNKNOWN')),
ADD COLUMN IF NOT EXISTS confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
ADD COLUMN IF NOT EXISTS verification_status TEXT CHECK (verification_status IN ('VERIFIED', 'PROVISIONAL', 'CONTESTED', 'DEPRECATED')),
ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ;

-- Set defaults
UPDATE user_risks
SET
    source_authority = 'UNKNOWN',
    confidence_score = 0.7,
    verification_status = 'PROVISIONAL',
    last_verified_at = valid_from
WHERE source_authority IS NULL;

CREATE INDEX IF NOT EXISTS idx_risks_verification
ON user_risks(user_id, title, verification_status, valid_to);

-- ============================================================================
-- 3. UPGRADE user_company_context TABLE
-- ============================================================================

ALTER TABLE user_company_context
ADD COLUMN IF NOT EXISTS source_authority TEXT CHECK (source_authority IN ('ERP', 'PDF', 'CHAT', 'USER_UPLOAD', 'API', 'UNKNOWN')),
ADD COLUMN IF NOT EXISTS confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
ADD COLUMN IF NOT EXISTS verification_status TEXT CHECK (verification_status IN ('VERIFIED', 'PROVISIONAL', 'CONTESTED', 'DEPRECATED')),
ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ;

-- Set defaults
UPDATE user_company_context
SET
    source_authority = 'UNKNOWN',
    confidence_score = 0.8,  -- Company context usually high confidence
    verification_status = 'PROVISIONAL',
    last_verified_at = valid_from
WHERE source_authority IS NULL;

CREATE INDEX IF NOT EXISTS idx_company_context_verification
ON user_company_context(user_id, key, verification_status);

-- ============================================================================
-- 4. UPGRADE user_conversational_memory TABLE
-- ============================================================================

-- Add source tracking for conversations
ALTER TABLE user_conversational_memory
ADD COLUMN IF NOT EXISTS source_authority TEXT DEFAULT 'CHAT',
ADD COLUMN IF NOT EXISTS was_corrected BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS correction_note TEXT;

-- ============================================================================
-- 5. CREATE fact_conflicts TABLE (New - for conflict tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- The contested fact
    fact_table TEXT NOT NULL,  -- Which table: 'user_business_facts', 'user_risks', etc.
    fact_id UUID NOT NULL,      -- ID of the contested fact

    -- Conflict details
    conflict_type TEXT CHECK (conflict_type IN ('VALUE_MISMATCH', 'TEMPORAL_OVERLAP', 'LOGICAL_CONTRADICTION')),
    conflicting_fact_id UUID,   -- ID of the fact it conflicts with

    -- Resolution
    resolution_status TEXT DEFAULT 'PENDING' CHECK (resolution_status IN ('PENDING', 'USER_RESOLVED', 'AUTO_RESOLVED', 'IGNORED')),
    resolution_method TEXT,     -- How was it resolved: 'USER_CHOICE', 'SOURCE_PRIORITY', 'RECENCY', etc.
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,           -- 'USER', 'SYSTEM'

    -- Metadata
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    details JSONB,              -- Store conflict details (old_value, new_value, etc.)

    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fact_conflicts_pending
ON fact_conflicts(user_id, resolution_status, detected_at);

-- ============================================================================
-- 6. CREATE sql_memory TABLE (New - for procedural memory / CBR)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sql_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,

    -- The natural language question
    natural_question TEXT NOT NULL,
    natural_question_embedding vector(768),  -- For similarity search

    -- The successful SQL query
    sql_template TEXT NOT NULL,
    sql_type TEXT CHECK (sql_type IN ('SELECT', 'AGGREGATE', 'JOIN', 'WINDOW', 'CTE', 'OTHER')),

    -- Schema context (what tables/columns were used)
    tables_used TEXT[],
    columns_used TEXT[],
    schema_snapshot JSONB,  -- Store relevant schema at time of creation

    -- Success tracking
    success_count INT DEFAULT 1,
    failure_count INT DEFAULT 0,
    avg_execution_time_ms FLOAT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 1.0,

    -- Versioning (if schema changes, old queries may become invalid)
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecated_reason TEXT,

    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sql_memory_embedding
ON sql_memory USING ivfflat (natural_question_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_sql_memory_user
ON sql_memory(user_id, is_deprecated, success_count DESC);

-- ============================================================================
-- 7. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to search sql_memory by similarity
CREATE OR REPLACE FUNCTION match_sql_templates(
    query_embedding vector(768),
    match_count int DEFAULT 5,
    p_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    natural_question text,
    sql_template text,
    sql_type text,
    tables_used text[],
    success_count int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        sql_memory.id,
        sql_memory.natural_question,
        sql_memory.sql_template,
        sql_memory.sql_type,
        sql_memory.tables_used,
        sql_memory.success_count,
        1 - (sql_memory.natural_question_embedding <=> query_embedding) AS similarity
    FROM sql_memory
    WHERE
        (p_user_id IS NULL OR sql_memory.user_id = p_user_id)
        AND sql_memory.is_deprecated = FALSE
        AND sql_memory.natural_question_embedding IS NOT NULL
    ORDER BY sql_memory.natural_question_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get active (non-deprecated) facts
CREATE OR REPLACE FUNCTION get_active_facts(
    p_user_id uuid,
    p_subject text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    subject text,
    predicate text,
    value text,
    confidence_score float,
    verification_status text,
    valid_from timestamptz,
    valid_to timestamptz
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
        user_business_facts.confidence_score,
        user_business_facts.verification_status,
        user_business_facts.valid_from,
        user_business_facts.valid_to
    FROM user_business_facts
    WHERE
        user_business_facts.user_id = p_user_id
        AND (p_subject IS NULL OR user_business_facts.subject ILIKE '%' || p_subject || '%')
        AND (user_business_facts.valid_to IS NULL OR user_business_facts.valid_to > NOW())
        AND user_business_facts.verification_status != 'DEPRECATED'
    ORDER BY user_business_facts.confidence_score DESC, user_business_facts.valid_from DESC;
END;
$$;

-- ============================================================================
-- 8. VERIFICATION QUERIES
-- ============================================================================

-- Check that all columns were added successfully
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('user_business_facts', 'user_risks', 'user_company_context', 'sql_memory', 'fact_conflicts')
  AND column_name IN ('source_authority', 'confidence_score', 'verification_status', 'valid_to')
ORDER BY table_name, column_name;

-- Summary of upgrade
SELECT
    'user_business_facts' as table_name,
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE verification_status = 'VERIFIED') as verified,
    COUNT(*) FILTER (WHERE verification_status = 'PROVISIONAL') as provisional,
    COUNT(*) FILTER (WHERE verification_status = 'CONTESTED') as contested
FROM user_business_facts
UNION ALL
SELECT
    'user_risks',
    COUNT(*),
    COUNT(*) FILTER (WHERE verification_status = 'VERIFIED'),
    COUNT(*) FILTER (WHERE verification_status = 'PROVISIONAL'),
    COUNT(*) FILTER (WHERE verification_status = 'CONTESTED')
FROM user_risks
UNION ALL
SELECT
    'user_company_context',
    COUNT(*),
    COUNT(*) FILTER (WHERE verification_status = 'VERIFIED'),
    COUNT(*) FILTER (WHERE verification_status = 'PROVISIONAL'),
    COUNT(*) FILTER (WHERE verification_status = 'CONTESTED')
FROM user_company_context;

-- ============================================================================
-- UPGRADE COMPLETE!
-- ============================================================================
-- Next steps:
-- 1. Update Python code to populate new columns during extraction
-- 2. Implement Truth Maintenance logic in memory_manager.py
-- 3. Implement SQL template storage/retrieval in procedural memory
-- ============================================================================
