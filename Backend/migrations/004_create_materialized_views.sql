-- ============================================================================
-- KPI Extraction System - Materialized Views
-- ============================================================================
-- This migration creates materialized views for aggregated analytics and
-- performance summaries. These views are refreshed hourly for optimal
-- performance while maintaining data freshness.
-- ============================================================================

-- ============================================================================
-- Materialized View 1: mv_agent_performance_summary
-- Purpose: Aggregates agent metrics by day/hour for fast analytics
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_agent_performance_summary AS
SELECT
    -- Time dimensions
    DATE_TRUNC('day', created_at) as date,
    DATE_TRUNC('hour', created_at) as hour,

    -- Grouping dimensions
    organization_id,
    agent_name,
    model_used,

    -- Count metrics
    COUNT(*) as execution_count,
    COUNT(*) FILTER (WHERE success = true) as successful_executions,
    COUNT(*) FILTER (WHERE success = false) as failed_executions,

    -- Response time metrics (in milliseconds)
    AVG(response_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as median_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,

    -- Token metrics
    SUM(token_count) as total_tokens,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    AVG(token_count) as avg_tokens_per_execution,

    -- Cost metrics
    SUM(estimated_cost_usd) as total_cost_usd,
    AVG(estimated_cost_usd) as avg_cost_per_execution_usd,

    -- Success rate
    ROUND(
        COUNT(*) FILTER (WHERE success = true)::DECIMAL /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as success_rate_percent,

    -- Confidence metrics
    AVG(confidence_score) as avg_confidence_score,
    MIN(confidence_score) as min_confidence_score,
    MAX(confidence_score) as max_confidence_score,

    -- Error tracking
    ARRAY_AGG(DISTINCT error_type) FILTER (WHERE error_type IS NOT NULL) as error_types,

    -- Metadata
    MIN(created_at) as period_start,
    MAX(created_at) as period_end,
    NOW() as last_refreshed
FROM
    agent_performance_metrics
GROUP BY
    DATE_TRUNC('day', created_at),
    DATE_TRUNC('hour', created_at),
    organization_id,
    agent_name,
    model_used;

-- Create indexes on the materialized view
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_date ON mv_agent_performance_summary(date);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_hour ON mv_agent_performance_summary(hour);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_org ON mv_agent_performance_summary(organization_id);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_agent ON mv_agent_performance_summary(agent_name);
CREATE INDEX IF NOT EXISTS idx_mv_agent_perf_model ON mv_agent_performance_summary(model_used);

-- ============================================================================
-- Materialized View 2: mv_connector_kpi_trends
-- Purpose: Time-series view of all connector KPIs with trend analysis
-- ============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_connector_kpi_trends AS
WITH daily_kpis AS (
    SELECT
        DATE_TRUNC('day', extracted_at) as date,
        organization_id,
        connector_type,
        kpi_category,
        kpi_name,
        kpi_unit,
        source_id,
        source_name,

        -- Get the latest value for the day
        (ARRAY_AGG(kpi_value ORDER BY extracted_at DESC))[1] as latest_kpi_value,

        -- Statistical aggregations (for numeric values)
        COUNT(*) as sample_count,
        MIN(extracted_at) as first_extraction,
        MAX(extracted_at) as last_extraction,

        -- Period info
        MIN(period_start) as period_start,
        MAX(period_end) as period_end
    FROM
        connector_kpis
    GROUP BY
        DATE_TRUNC('day', extracted_at),
        organization_id,
        connector_type,
        kpi_category,
        kpi_name,
        kpi_unit,
        source_id,
        source_name
),
kpi_with_trends AS (
    SELECT
        *,
        -- Calculate day-over-day change (if numeric value)
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number' THEN
                latest_kpi_value::TEXT::NUMERIC -
                LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                    PARTITION BY organization_id, connector_type, kpi_name, source_id
                    ORDER BY date
                )
            ELSE NULL
        END as day_over_day_change,

        -- Calculate trend direction
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number' THEN
                CASE
                    WHEN latest_kpi_value::TEXT::NUMERIC >
                         COALESCE(LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                             PARTITION BY organization_id, connector_type, kpi_name, source_id
                             ORDER BY date
                         ), 0) THEN 'up'
                    WHEN latest_kpi_value::TEXT::NUMERIC <
                         COALESCE(LAG(latest_kpi_value::TEXT::NUMERIC) OVER (
                             PARTITION BY organization_id, connector_type, kpi_name, source_id
                             ORDER BY date
                         ), 0) THEN 'down'
                    ELSE 'stable'
                END
            ELSE 'n/a'
        END as trend_direction,

        -- 7-day moving average (for numeric values)
        CASE
            WHEN jsonb_typeof(latest_kpi_value) = 'number' THEN
                AVG(latest_kpi_value::TEXT::NUMERIC) OVER (
                    PARTITION BY organization_id, connector_type, kpi_name, source_id
                    ORDER BY date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                )
            ELSE NULL
        END as moving_avg_7day,

        NOW() as last_refreshed
    FROM
        daily_kpis
)
SELECT * FROM kpi_with_trends;

-- Create indexes on the materialized view
CREATE INDEX IF NOT EXISTS idx_mv_connector_kpi_date ON mv_connector_kpi_trends(date);
CREATE INDEX IF NOT EXISTS idx_mv_connector_kpi_org ON mv_connector_kpi_trends(organization_id);
CREATE INDEX IF NOT EXISTS idx_mv_connector_kpi_type ON mv_connector_kpi_trends(connector_type);
CREATE INDEX IF NOT EXISTS idx_mv_connector_kpi_category ON mv_connector_kpi_trends(kpi_category);
CREATE INDEX IF NOT EXISTS idx_mv_connector_kpi_name ON mv_connector_kpi_trends(kpi_name);
CREATE INDEX IF NOT EXISTS idx_mv_connector_kpi_source ON mv_connector_kpi_trends(source_id);

-- ============================================================================
-- Part 3: Create Refresh Functions
-- ============================================================================

-- Function to refresh agent performance summary
CREATE OR REPLACE FUNCTION refresh_agent_performance_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_performance_summary;
    RAISE NOTICE 'mv_agent_performance_summary refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to refresh connector KPI trends
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
-- Part 4: Verification
-- ============================================================================
SELECT 'Materialized Views Created Successfully!' as status;

SELECT
    'mv_agent_performance_summary: Created' as view_status
UNION ALL
SELECT
    'mv_connector_kpi_trends: Created'
UNION ALL
SELECT
    'Refresh functions: Created';

-- ============================================================================
-- Part 5: Usage Instructions
-- ============================================================================
-- To manually refresh the views, run:
-- SELECT refresh_all_kpi_views();
--
-- To set up automatic hourly refresh, create a cron job or use pg_cron:
-- SELECT cron.schedule('refresh-kpi-views', '0 * * * *', 'SELECT refresh_all_kpi_views()');
-- ============================================================================
