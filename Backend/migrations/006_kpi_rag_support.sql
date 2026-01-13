-- Migration 006: KPI RAG Support
-- Adds support for embedding KPI summaries into the vector database
-- and querying KPI trend data efficiently

-- =====================================================
-- 1. Add metadata column to document_chunks
-- =====================================================

-- Add metadata JSONB column if it doesn't exist
-- This allows us to store additional information about embedded documents
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'document_chunks'
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE document_chunks
        ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;

        RAISE NOTICE 'Added metadata column to document_chunks';
    ELSE
        RAISE NOTICE 'metadata column already exists in document_chunks';
    END IF;
END $$;

-- =====================================================
-- 2. Create indexes for efficient KPI document filtering
-- =====================================================

-- Index for filtering by document type (e.g., 'kpi_summary')
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_doc_type
ON document_chunks ((metadata->>'document_type'));

-- Index for filtering by KPI category (velocity, burndown, etc.)
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_kpi_category
ON document_chunks ((metadata->>'kpi_category'));

-- Index for filtering by connector type
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_connector_type
ON document_chunks ((metadata->>'connector_type'));

-- Composite index for KPI-specific queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_kpi_composite
ON document_chunks (user_id, (metadata->>'document_type'), (metadata->>'connector_type'))
WHERE (metadata->>'document_type') = 'kpi_summary';

-- =====================================================
-- 3. Create RPC function for efficient KPI trend retrieval
-- =====================================================

-- This function is used by the kpi_summary_service to fetch trend data
-- for embedding natural language summaries

CREATE OR REPLACE FUNCTION get_kpi_trend(
    p_organization_id UUID,
    p_connector_type VARCHAR,
    p_source_id VARCHAR,
    p_kpi_name VARCHAR,
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    trend_direction VARCHAR,
    day_over_day_change DECIMAL,
    moving_avg_7day DECIMAL,
    sample_count INTEGER,
    latest_value JSONB,
    date DATE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.trend_direction,
        t.day_over_day_change,
        t.moving_avg_7day,
        t.sample_count,
        t.latest_kpi_value as latest_value,
        t.date
    FROM mv_connector_kpi_trends t
    WHERE t.organization_id = p_organization_id
        AND t.connector_type = p_connector_type
        AND t.source_id = p_source_id
        AND t.kpi_name = p_kpi_name
        AND t.date >= CURRENT_DATE - p_days_back
    ORDER BY t.date DESC
    LIMIT 1;
END;
$$;

-- Add comment explaining the function
COMMENT ON FUNCTION get_kpi_trend IS
'Retrieves the latest trend data for a specific KPI from the materialized view.
Used by kpi_summary_service to generate natural language summaries with trend analysis.';

-- =====================================================
-- 4. Create helper function for bulk KPI embedding status
-- =====================================================

-- This function helps monitor which KPIs have been embedded
CREATE OR REPLACE FUNCTION get_kpi_embedding_status(
    p_organization_id UUID,
    p_connector_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    kpi_id INTEGER,
    kpi_name VARCHAR,
    connector_type VARCHAR,
    source_id VARCHAR,
    source_name VARCHAR,
    has_embedding BOOLEAN,
    kpi_created_at TIMESTAMP,
    embedding_created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.id as kpi_id,
        k.kpi_name,
        k.connector_type,
        k.source_id,
        k.source_name,
        CASE
            WHEN d.file_path IS NOT NULL THEN TRUE
            ELSE FALSE
        END as has_embedding,
        k.created_at as kpi_created_at,
        d.created_at as embedding_created_at
    FROM connector_kpis k
    LEFT JOIN document_chunks d
        ON d.file_path LIKE 'kpi://' || k.connector_type || '/' || k.source_id || '/' || k.kpi_name || '/%'
        AND d.user_id = k.user_id
    WHERE k.organization_id = p_organization_id
        AND (p_connector_type IS NULL OR k.connector_type = p_connector_type)
    ORDER BY k.created_at DESC;
END;
$$;

COMMENT ON FUNCTION get_kpi_embedding_status IS
'Returns embedding status for all KPIs in an organization.
Useful for monitoring and debugging the KPI embedding pipeline.';

-- =====================================================
-- 5. Create view for KPI embedding health metrics
-- =====================================================

CREATE OR REPLACE VIEW v_kpi_embedding_health AS
SELECT
    k.organization_id,
    k.connector_type,
    COUNT(DISTINCT k.id) as total_kpis,
    COUNT(DISTINCT d.file_path) as embedded_kpis,
    ROUND(
        100.0 * COUNT(DISTINCT d.file_path) / NULLIF(COUNT(DISTINCT k.id), 0),
        2
    ) as embedding_coverage_pct,
    MAX(k.created_at) as latest_kpi_created_at,
    MAX(d.created_at) as latest_embedding_created_at
FROM connector_kpis k
LEFT JOIN document_chunks d
    ON d.file_path LIKE 'kpi://' || k.connector_type || '/%'
    AND d.user_id = k.user_id
    AND (d.metadata->>'document_type') = 'kpi_summary'
GROUP BY k.organization_id, k.connector_type;

COMMENT ON VIEW v_kpi_embedding_health IS
'Provides aggregated health metrics for KPI embeddings by organization and connector type.
Use this to monitor embedding coverage and identify gaps.';

-- =====================================================
-- 6. Grant permissions (if using RLS)
-- =====================================================

-- Grant execute permissions on the functions to authenticated users
-- Adjust these based on your Supabase RLS policies

-- GRANT EXECUTE ON FUNCTION get_kpi_trend TO authenticated;
-- GRANT EXECUTE ON FUNCTION get_kpi_embedding_status TO authenticated;
-- GRANT SELECT ON v_kpi_embedding_health TO authenticated;

-- =====================================================
-- Migration Complete
-- =====================================================

-- Verify the migration
DO $$
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Migration 006: KPI RAG Support - COMPLETED';
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Changes applied:';
    RAISE NOTICE '1. Added metadata column to document_chunks';
    RAISE NOTICE '2. Created indexes for KPI document filtering';
    RAISE NOTICE '3. Created get_kpi_trend() RPC function';
    RAISE NOTICE '4. Created get_kpi_embedding_status() helper function';
    RAISE NOTICE '5. Created v_kpi_embedding_health monitoring view';
    RAISE NOTICE '=================================================';
END $$;
