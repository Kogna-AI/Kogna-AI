-- ============================================================================
-- Phase 2: Fix Materialized Views with Team ID Aggregation
-- ============================================================================
-- This migration fixes the materialized views to properly support:
-- 1. Team ID aggregation in GROUP BY clauses
-- 2. Unique indexes for CONCURRENT refresh support
-- 3. Correct window function calculations for trends
--
-- Fixes Issues:
-- - Previous mv_connector_kpi_trends had incorrect GROUP BY (included kpi_value)
-- - Missing unique indexes prevented CONCURRENT refresh
-- ============================================================================

-- ============================================================================
-- Part 1: Drop existing materialized views and their indexes
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_agent_performance_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_connector_kpi_trends CASCADE;

-- ============================================================================
-- Part 2: Recreate mv_agent_performance_summary with team_id
-- ============================================================================

CREATE MATERIALIZED VIEW mv_agent_performance_summary AS
SELECT
    -- Time dimensions
    DATE(started_at) as date,
    DATE_TRUNC('hour', started_at) as hour,

    -- Grouping dimensions (including team_id for RBAC)
    organization_id,
    team_id,
    agent_name,
    model_used,

    -- Execution counts
    COUNT(*) as execution_count,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_executions,

    -- Response time metrics (in milliseconds)
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
    ROUND(
        (SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / NULLIF(COUNT(*), 0) * 100),
        2
    ) as success_rate_percent,

    -- Confidence scores
    AVG(confidence_score) as avg_confidence_score,
    MIN(confidence_score) as min_confidence_score,
    MAX(confidence_score) as max_confidence_score,

    -- Error tracking
    ARRAY_AGG(DISTINCT error_type) FILTER (WHERE error_type IS NOT NULL) as error_types,

    -- Time range metadata
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

-- ============================================================================
-- Part 3: Create indexes for mv_agent_performance_summary
-- ============================================================================

-- Standard lookup indexes
CREATE INDEX idx_mv_agent_perf_date ON mv_agent_performance_summary(date);
CREATE INDEX idx_mv_agent_perf_hour ON mv_agent_performance_summary(hour);
CREATE INDEX idx_mv_agent_perf_organization_id ON mv_agent_performance_summary(organization_id);
CREATE INDEX idx_mv_agent_perf_team_id ON mv_agent_performance_summary(team_id);
CREATE INDEX idx_mv_agent_perf_agent_name ON mv_agent_performance_summary(agent_name);
CREATE INDEX idx_mv_agent_perf_model ON mv_agent_performance_summary(model_used);

-- Composite index for common queries (org + team filtering)
CREATE INDEX idx_mv_agent_perf_org_team ON mv_agent_performance_summary(organization_id, team_id);
CREATE INDEX idx_mv_agent_perf_org_team_date ON mv_agent_performance_summary(organization_id, team_id, date);

-- UNIQUE INDEX for CONCURRENT refresh support
-- Uses COALESCE to handle NULL team_id values
CREATE UNIQUE INDEX idx_mv_agent_perf_unique ON mv_agent_performance_summary(
    date,
    hour,
    organization_id,
    COALESCE(team_id, '00000000-0000-0000-0000-000000000000'::UUID),
    COALESCE(agent_name, ''),
    COALESCE(model_used, '')
);

-- ============================================================================
-- Part 4: Recreate mv_connector_kpi_trends with team_id (FIXED)
-- ============================================================================

CREATE MATERIALIZED VIEW mv_connector_kpi_trends AS
WITH daily_kpis AS (
    -- First, aggregate to get daily latest values per KPI
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

        -- Get the latest value for each day (using window function)
        FIRST_VALUE(kpi_value) OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
            ORDER BY extracted_at DESC
        ) as latest_kpi_value,

        -- Count extractions per day
        COUNT(*) OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
        ) as sample_count,

        -- Period info
        MIN(period_start) OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
        ) as period_start,
        MAX(period_end) OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
        ) as period_end,

        MIN(extracted_at) OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
        ) as first_extraction,
        MAX(extracted_at) OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
        ) as last_extraction,

        -- Row number to deduplicate
        ROW_NUMBER() OVER (
            PARTITION BY DATE(extracted_at), organization_id, team_id, connector_type, kpi_name, source_id
            ORDER BY extracted_at DESC
        ) as rn
    FROM connector_kpis
),
deduplicated_daily AS (
    -- Keep only one row per day per KPI combination
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
        latest_kpi_value,
        sample_count,
        period_start,
        period_end,
        first_extraction,
        last_extraction
    FROM daily_kpis
    WHERE rn = 1
),
kpi_with_trends AS (
    -- Calculate trends using LAG window functions
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
        latest_kpi_value,
        sample_count,
        period_start,
        period_end,
        first_extraction,
        last_extraction,

        -- Day-over-day change (for numeric values)
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number' THEN
                (latest_kpi_value::TEXT::NUMERIC) -
                LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                    PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                    ORDER BY date
                )
            ELSE NULL
        END as day_over_day_change,

        -- Trend direction
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number' THEN
                CASE
                    WHEN (latest_kpi_value::TEXT::NUMERIC) >
                         COALESCE(LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                             PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                             ORDER BY date
                         ), latest_kpi_value::TEXT::NUMERIC) THEN 'up'
                    WHEN (latest_kpi_value::TEXT::NUMERIC) <
                         COALESCE(LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                             PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                             ORDER BY date
                         ), latest_kpi_value::TEXT::NUMERIC) THEN 'down'
                    ELSE 'stable'
                END
            ELSE 'n/a'
        END as trend_direction,

        -- 7-day moving average (for numeric values)
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number' THEN
                AVG(latest_kpi_value::TEXT::NUMERIC) OVER (
                    PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                    ORDER BY date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                )
            ELSE NULL
        END as moving_avg_7day,

        -- Percent change (for numeric values)
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number'
                 AND LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                     PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                     ORDER BY date
                 ) != 0 THEN
                ROUND(
                    ((latest_kpi_value::TEXT::NUMERIC) -
                     LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                         PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                         ORDER BY date
                     )) /
                    ABS(LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                        PARTITION BY organization_id, team_id, connector_type, kpi_name, source_id
                        ORDER BY date
                    )) * 100,
                    2
                )
            ELSE NULL
        END as percent_change,

        NOW() as last_refreshed
    FROM deduplicated_daily
)
SELECT * FROM kpi_with_trends;

-- ============================================================================
-- Part 5: Create indexes for mv_connector_kpi_trends
-- ============================================================================

-- Standard lookup indexes
CREATE INDEX idx_mv_connector_trends_date ON mv_connector_kpi_trends(date);
CREATE INDEX idx_mv_connector_trends_organization_id ON mv_connector_kpi_trends(organization_id);
CREATE INDEX idx_mv_connector_trends_team_id ON mv_connector_kpi_trends(team_id);
CREATE INDEX idx_mv_connector_trends_connector_type ON mv_connector_kpi_trends(connector_type);
CREATE INDEX idx_mv_connector_trends_kpi_category ON mv_connector_kpi_trends(kpi_category);
CREATE INDEX idx_mv_connector_trends_kpi_name ON mv_connector_kpi_trends(kpi_name);
CREATE INDEX idx_mv_connector_trends_source_id ON mv_connector_kpi_trends(source_id);

-- Composite indexes for common queries
CREATE INDEX idx_mv_connector_trends_org_team ON mv_connector_kpi_trends(organization_id, team_id);
CREATE INDEX idx_mv_connector_trends_org_team_date ON mv_connector_kpi_trends(organization_id, team_id, date);
CREATE INDEX idx_mv_connector_trends_org_connector ON mv_connector_kpi_trends(organization_id, connector_type);

-- UNIQUE INDEX for CONCURRENT refresh support
-- Uses COALESCE to handle NULL values
CREATE UNIQUE INDEX idx_mv_connector_trends_unique ON mv_connector_kpi_trends(
    date,
    organization_id,
    COALESCE(team_id, '00000000-0000-0000-0000-000000000000'::UUID),
    connector_type,
    kpi_name,
    source_id
);

-- ============================================================================
-- Part 6: Update refresh functions
-- ============================================================================

-- Drop existing functions to recreate
DROP FUNCTION IF EXISTS refresh_agent_performance_summary();
DROP FUNCTION IF EXISTS refresh_connector_kpi_trends();
DROP FUNCTION IF EXISTS refresh_all_kpi_views();

-- Function to refresh agent performance summary (CONCURRENT for zero-downtime)
CREATE OR REPLACE FUNCTION refresh_agent_performance_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_performance_summary;
    RAISE NOTICE 'mv_agent_performance_summary refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to refresh connector KPI trends (CONCURRENT for zero-downtime)
CREATE OR REPLACE FUNCTION refresh_connector_kpi_trends()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_connector_kpi_trends;
    RAISE NOTICE 'mv_connector_kpi_trends refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_kpi_views()
RETURNS void AS $$
BEGIN
    PERFORM refresh_agent_performance_summary();
    PERFORM refresh_connector_kpi_trends();
    RAISE NOTICE 'All KPI materialized views refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 7: Initial refresh of materialized views
-- ============================================================================

-- Note: First refresh must be non-concurrent since views are empty
-- Subsequent refreshes can use CONCURRENT

-- Check if there's data before attempting refresh
DO $$
DECLARE
    v_agent_count INTEGER;
    v_kpi_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_agent_count FROM agent_performance_metrics LIMIT 1;
    SELECT COUNT(*) INTO v_kpi_count FROM connector_kpis LIMIT 1;

    IF v_agent_count > 0 THEN
        REFRESH MATERIALIZED VIEW mv_agent_performance_summary;
        RAISE NOTICE 'Initial refresh of mv_agent_performance_summary completed';
    ELSE
        RAISE NOTICE 'mv_agent_performance_summary: No data to refresh (agent_performance_metrics is empty)';
    END IF;

    IF v_kpi_count > 0 THEN
        REFRESH MATERIALIZED VIEW mv_connector_kpi_trends;
        RAISE NOTICE 'Initial refresh of mv_connector_kpi_trends completed';
    ELSE
        RAISE NOTICE 'mv_connector_kpi_trends: No data to refresh (connector_kpis is empty)';
    END IF;
END $$;

-- ============================================================================
-- Part 8: Verification
-- ============================================================================

SELECT 'Materialized views with team_id aggregation created successfully!' as status;

-- Verify materialized views exist
SELECT
    schemaname,
    matviewname,
    hasindexes,
    ispopulated
FROM pg_matviews
WHERE schemaname = 'public'
    AND matviewname IN ('mv_agent_performance_summary', 'mv_connector_kpi_trends');

-- Verify unique indexes exist (required for CONCURRENT refresh)
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('mv_agent_performance_summary', 'mv_connector_kpi_trends')
    AND indexname LIKE '%unique%';

-- Verify team_id is included in both views
SELECT
    'mv_agent_performance_summary' as view_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'mv_agent_performance_summary'
    AND column_name = 'team_id'
UNION ALL
SELECT
    'mv_connector_kpi_trends',
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'mv_connector_kpi_trends'
    AND column_name = 'team_id';

-- ============================================================================
-- Part 9: Usage Instructions
-- ============================================================================

/*
USAGE NOTES:

1. Manual Refresh:
   SELECT refresh_all_kpi_views();

   Or individually:
   SELECT refresh_agent_performance_summary();
   SELECT refresh_connector_kpi_trends();

2. Automatic Hourly Refresh (using pg_cron):
   SELECT cron.schedule('refresh-kpi-views', '0 * * * *', 'SELECT refresh_all_kpi_views()');

3. Querying with team_id filter:

   -- Get agent performance for a specific team
   SELECT * FROM mv_agent_performance_summary
   WHERE organization_id = 'your-org-id'
     AND team_id = 'your-team-id'
     AND date >= CURRENT_DATE - INTERVAL '7 days';

   -- Get KPI trends for a specific team
   SELECT * FROM mv_connector_kpi_trends
   WHERE organization_id = 'your-org-id'
     AND team_id = 'your-team-id'
     AND connector_type = 'jira'
   ORDER BY date DESC;

4. Querying across all teams (org-level view):
   SELECT * FROM mv_agent_performance_summary
   WHERE organization_id = 'your-org-id'
     AND date >= CURRENT_DATE - INTERVAL '7 days';

5. Aggregating by team:
   SELECT
       team_id,
       SUM(execution_count) as total_executions,
       AVG(avg_response_time_ms) as avg_response_time
   FROM mv_agent_performance_summary
   WHERE organization_id = 'your-org-id'
   GROUP BY team_id;
*/

-- ============================================================================
-- End of Migration
-- ============================================================================
