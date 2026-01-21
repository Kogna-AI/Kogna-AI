-- ============================================================================
-- Phase 1: Add team_id to KPI Extraction System for RBAC
-- ============================================================================
-- This migration adds team_id columns to all KPI-related tables to enable
-- proper team-level RBAC and multi-tenant isolation.
--
-- Tables Modified:
-- - connector_kpis
-- - agent_performance_metrics
-- - user_engagement_metrics
-- - rag_quality_metrics
-- - sync_jobs (if exists from migrations/003)
-- ============================================================================

-- ============================================================================
-- Part 1: Add team_id columns to KPI tables
-- ============================================================================

-- Add team_id to connector_kpis
-- ============================================================================
ALTER TABLE connector_kpis
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- Add team_id to agent_performance_metrics
-- ============================================================================
ALTER TABLE agent_performance_metrics
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- Add team_id to user_engagement_metrics
-- ============================================================================
ALTER TABLE user_engagement_metrics
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- Add organization_id and team_id to rag_quality_metrics
-- ============================================================================
ALTER TABLE rag_quality_metrics
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE rag_quality_metrics
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- Add team_id to sync_jobs (if table exists)
-- ============================================================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sync_jobs') THEN
        ALTER TABLE sync_jobs
        ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- Part 2: Create indexes for team_id columns
-- ============================================================================

-- Indexes for connector_kpis
CREATE INDEX IF NOT EXISTS idx_connector_kpis_team_id ON connector_kpis(team_id);
CREATE INDEX IF NOT EXISTS idx_connector_kpis_org_team ON connector_kpis(organization_id, team_id);

-- Indexes for agent_performance_metrics
CREATE INDEX IF NOT EXISTS idx_agent_performance_team_id ON agent_performance_metrics(team_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_org_team ON agent_performance_metrics(organization_id, team_id);

-- Indexes for user_engagement_metrics
CREATE INDEX IF NOT EXISTS idx_user_engagement_team_id ON user_engagement_metrics(team_id);
CREATE INDEX IF NOT EXISTS idx_user_engagement_org_team ON user_engagement_metrics(organization_id, team_id);

-- Indexes for rag_quality_metrics
CREATE INDEX IF NOT EXISTS idx_rag_quality_organization_id ON rag_quality_metrics(organization_id);
CREATE INDEX IF NOT EXISTS idx_rag_quality_team_id ON rag_quality_metrics(team_id);
CREATE INDEX IF NOT EXISTS idx_rag_quality_org_team ON rag_quality_metrics(organization_id, team_id);

-- Indexes for sync_jobs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sync_jobs') THEN
        CREATE INDEX IF NOT EXISTS idx_sync_jobs_team_id ON sync_jobs(team_id);
        CREATE INDEX IF NOT EXISTS idx_sync_jobs_org_team ON sync_jobs(organization_id, team_id);
    END IF;
END $$;

-- ============================================================================
-- Part 3: Update constraints for connector_kpis
-- ============================================================================

-- Drop old unique constraint and create new one that includes team_id
-- This allows the same KPI to exist for different teams
ALTER TABLE connector_kpis
DROP CONSTRAINT IF EXISTS connector_kpis_user_id_connector_type_source_id_kpi_name_key;

-- Add new unique constraint with team_id
-- Note: Using COALESCE to handle NULL team_id values in unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_connector_kpis_unique_with_team
ON connector_kpis (
    organization_id,
    COALESCE(team_id, '00000000-0000-0000-0000-000000000000'::UUID),
    connector_type,
    source_id,
    kpi_name,
    period_start
);

-- ============================================================================
-- Part 4: Update constraints for user_engagement_metrics
-- ============================================================================

-- Drop old unique constraint
ALTER TABLE user_engagement_metrics
DROP CONSTRAINT IF EXISTS user_engagement_metrics_user_id_date_key;

-- Add new unique constraint with team_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_engagement_unique_with_team
ON user_engagement_metrics (
    user_id,
    organization_id,
    COALESCE(team_id, '00000000-0000-0000-0000-000000000000'::UUID),
    date
);

-- ============================================================================
-- Part 5: Add audit logging column to audit_logs (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        ALTER TABLE audit_logs
        ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

        CREATE INDEX IF NOT EXISTS idx_audit_logs_team_id ON audit_logs(team_id);
    END IF;
END $$;

-- ============================================================================
-- Part 6: Rebuild materialized views with team_id
-- ============================================================================

-- Drop existing materialized views if they exist
DROP MATERIALIZED VIEW IF EXISTS mv_agent_performance_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_connector_kpi_trends CASCADE;

-- Recreate mv_agent_performance_summary with team_id
-- ============================================================================
CREATE MATERIALIZED VIEW mv_agent_performance_summary AS
SELECT
    DATE(started_at) as date,
    DATE_TRUNC('hour', started_at) as hour,
    organization_id,
    team_id,
    agent_name,
    model_used,

    -- Execution counts
    COUNT(*) as execution_count,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_executions,

    -- Response time metrics
    AVG(response_time_ms)::FLOAT as avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms)::FLOAT as median_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms)::FLOAT as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms)::FLOAT as p99_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,

    -- Token usage metrics
    SUM(token_count) as total_tokens,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    AVG(token_count)::FLOAT as avg_tokens_per_execution,

    -- Cost metrics
    SUM(estimated_cost_usd) as total_cost_usd,
    AVG(estimated_cost_usd) as avg_cost_per_execution_usd,

    -- Success rate
    (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100) as success_rate_percent,

    -- Confidence scores
    AVG(confidence_score) as avg_confidence_score,
    MIN(confidence_score) as min_confidence_score,
    MAX(confidence_score) as max_confidence_score,

    -- Error tracking
    ARRAY_AGG(DISTINCT error_type) FILTER (WHERE error_type IS NOT NULL) as error_types,

    -- Time range
    MIN(started_at) as period_start,
    MAX(completed_at) as period_end,
    NOW() as last_refreshed
FROM agent_performance_metrics
GROUP BY
    DATE(started_at),
    DATE_TRUNC('hour', started_at),
    organization_id,
    team_id,
    agent_name,
    model_used;

-- Create indexes for mv_agent_performance_summary
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_date ON mv_agent_performance_summary(date);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_hour ON mv_agent_performance_summary(hour);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_organization_id ON mv_agent_performance_summary(organization_id);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_team_id ON mv_agent_performance_summary(team_id);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_agent_name ON mv_agent_performance_summary(agent_name);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_model ON mv_agent_performance_summary(model_used);

-- Recreate mv_connector_kpi_trends with team_id
-- ============================================================================
CREATE MATERIALIZED VIEW mv_connector_kpi_trends AS
WITH kpi_data AS (
    SELECT
        DATE(extracted_at) as date,
        organization_id,
        team_id,
        connector_type,
        kpi_category,
        kpi_name,
        kpi_unit,
        source_id,
        source_name,
        kpi_value,
        extracted_at,
        period_start,
        period_end,
        ROW_NUMBER() OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_category, kpi_name, source_id
            ORDER BY extracted_at DESC
        ) as rn
    FROM connector_kpis
)
SELECT
    date,
    organization_id,
    team_id,
    connector_type,
    kpi_category,
    kpi_name,
    kpi_unit,
    source_id,
    source_name,
    kpi_value as latest_kpi_value,
    COUNT(*) as sample_count,
    MIN(extracted_at) as first_extraction,
    MAX(extracted_at) as last_extraction,
    MIN(period_start) as period_start,
    MAX(period_end) as period_end,

    -- Day-over-day change calculation (for numeric values)
    CASE
        WHEN jsonb_typeof(kpi_value) = 'number' THEN
            kpi_value::text::NUMERIC - LAG(kpi_value::text::NUMERIC) OVER (
                PARTITION BY organization_id, team_id, connector_type, kpi_category, kpi_name, source_id
                ORDER BY date
            )
        ELSE NULL
    END as day_over_day_change,

    -- Trend direction
    CASE
        WHEN jsonb_typeof(kpi_value) = 'number' THEN
            CASE
                WHEN kpi_value::text::NUMERIC > LAG(kpi_value::text::NUMERIC) OVER (
                    PARTITION BY organization_id, team_id, connector_type, kpi_category, kpi_name, source_id
                    ORDER BY date
                ) THEN 'up'
                WHEN kpi_value::text::NUMERIC < LAG(kpi_value::text::NUMERIC) OVER (
                    PARTITION BY organization_id, team_id, connector_type, kpi_category, kpi_name, source_id
                    ORDER BY date
                ) THEN 'down'
                ELSE 'stable'
            END
        ELSE 'n/a'
    END as trend_direction,

    -- 7-day moving average (for numeric values)
    CASE
        WHEN jsonb_typeof(kpi_value) = 'number' THEN
            AVG(kpi_value::text::NUMERIC) OVER (
                PARTITION BY organization_id, team_id, connector_type, kpi_category, kpi_name, source_id
                ORDER BY date
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            )
        ELSE NULL
    END as moving_avg_7day,

    NOW() as last_refreshed
FROM kpi_data
WHERE rn = 1
GROUP BY
    date,
    organization_id,
    team_id,
    connector_type,
    kpi_category,
    kpi_name,
    kpi_unit,
    source_id,
    source_name,
    kpi_value,
    extracted_at;

-- Create indexes for mv_connector_kpi_trends
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_date ON mv_connector_kpi_trends(date);
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_organization_id ON mv_connector_kpi_trends(organization_id);
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_team_id ON mv_connector_kpi_trends(team_id);
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_connector_type ON mv_connector_kpi_trends(connector_type);
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_kpi_category ON mv_connector_kpi_trends(kpi_category);
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_kpi_name ON mv_connector_kpi_trends(kpi_name);
CREATE INDEX IF NOT EXISTS idx_mv_connector_trends_source_id ON mv_connector_kpi_trends(source_id);

-- ============================================================================
-- Part 7: Update refresh functions
-- ============================================================================

-- Drop and recreate refresh functions to handle new views
DROP FUNCTION IF EXISTS refresh_agent_performance_summary();
DROP FUNCTION IF EXISTS refresh_connector_kpi_trends();
DROP FUNCTION IF EXISTS refresh_all_kpi_views();

-- Create refresh function for agent performance summary
CREATE OR REPLACE FUNCTION refresh_agent_performance_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_performance_summary;
END;
$$ LANGUAGE plpgsql;

-- Create refresh function for connector KPI trends
CREATE OR REPLACE FUNCTION refresh_connector_kpi_trends()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_connector_kpi_trends;
END;
$$ LANGUAGE plpgsql;

-- Create convenience function to refresh all KPI views
CREATE OR REPLACE FUNCTION refresh_all_kpi_views()
RETURNS void AS $$
BEGIN
    PERFORM refresh_agent_performance_summary();
    PERFORM refresh_connector_kpi_trends();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 8: Verification
-- ============================================================================

SELECT 'Team RBAC columns added to KPI system successfully!' as status;

-- Verify team_id columns exist
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
    AND column_name = 'team_id'
    AND table_name IN (
        'connector_kpis',
        'agent_performance_metrics',
        'user_engagement_metrics',
        'rag_quality_metrics',
        'sync_jobs',
        'audit_logs'
    )
ORDER BY table_name;

-- Verify materialized views were recreated
SELECT
    schemaname,
    matviewname,
    hasindexes
FROM pg_matviews
WHERE schemaname = 'public'
    AND matviewname IN ('mv_agent_performance_summary', 'mv_connector_kpi_trends');
