-- =============================================================================
-- Migration 005: Phase 5 - Scheduled Reporting System Setup
-- =============================================================================
-- This migration creates the necessary database objects for the KPI scheduler:
-- 1. scheduler_logs table for tracking task executions
-- 2. kpi_reports table for report metadata
-- 3. Helper functions for materialized view refreshes
-- 4. Storage bucket for KPI reports
--
-- Run this migration in Supabase SQL Editor or via psql
-- =============================================================================

-- =============================================================================
-- Table 1: scheduler_logs
-- =============================================================================
-- Tracks execution of scheduled tasks (view refreshes, aggregations, reports, cleanup)

CREATE TABLE IF NOT EXISTS public.scheduler_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'partial_failure', 'failed')),
    execution_time_ms INTEGER NOT NULL,
    details JSONB DEFAULT '{}',
    executed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes for querying
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_scheduler_logs_task_name ON public.scheduler_logs(task_name);
CREATE INDEX IF NOT EXISTS idx_scheduler_logs_executed_at ON public.scheduler_logs(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_scheduler_logs_status ON public.scheduler_logs(status);

-- Add comments
COMMENT ON TABLE public.scheduler_logs IS 'Logs execution history of scheduled KPI tasks';
COMMENT ON COLUMN public.scheduler_logs.task_name IS 'Name of the scheduled task (e.g., refresh_materialized_views)';
COMMENT ON COLUMN public.scheduler_logs.status IS 'Execution status: success, partial_failure, or failed';
COMMENT ON COLUMN public.scheduler_logs.execution_time_ms IS 'Task execution duration in milliseconds';
COMMENT ON COLUMN public.scheduler_logs.details IS 'Additional execution details (errors, counts, etc.)';


-- =============================================================================
-- Table 2: kpi_reports
-- =============================================================================
-- Stores metadata about generated KPI reports (PDF/JSON files in storage)

CREATE TABLE IF NOT EXISTS public.kpi_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    file_path TEXT NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    summary JSONB DEFAULT '{}',

    -- Indexes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_kpi_reports_org_id ON public.kpi_reports(organization_id);
CREATE INDEX IF NOT EXISTS idx_kpi_reports_report_type ON public.kpi_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_kpi_reports_period ON public.kpi_reports(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_kpi_reports_generated_at ON public.kpi_reports(generated_at DESC);

-- Unique constraint: one report per organization per period
CREATE UNIQUE INDEX IF NOT EXISTS idx_kpi_reports_unique ON public.kpi_reports(
    organization_id, report_type, period_start, period_end
);

-- Add comments
COMMENT ON TABLE public.kpi_reports IS 'Metadata for generated weekly/monthly KPI reports';
COMMENT ON COLUMN public.kpi_reports.report_type IS 'Type of report (e.g., weekly_kpi_summary, monthly_overview)';
COMMENT ON COLUMN public.kpi_reports.file_path IS 'Path to report file in Supabase Storage';
COMMENT ON COLUMN public.kpi_reports.summary IS 'Quick summary of report contents (counts, highlights)';


-- =============================================================================
-- Table 3: Extend user_engagement_metrics (if columns missing)
-- =============================================================================
-- Ensure user_engagement_metrics has all required columns for Phase 5

DO $$
BEGIN
    -- Add top_topics column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'user_engagement_metrics'
        AND column_name = 'top_topics'
    ) THEN
        ALTER TABLE public.user_engagement_metrics
        ADD COLUMN top_topics TEXT[] DEFAULT ARRAY[]::TEXT[];
    END IF;

    -- Add period_start column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'user_engagement_metrics'
        AND column_name = 'period_start'
    ) THEN
        ALTER TABLE public.user_engagement_metrics
        ADD COLUMN period_start TIMESTAMPTZ;
    END IF;

    -- Add period_end column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'user_engagement_metrics'
        AND column_name = 'period_end'
    ) THEN
        ALTER TABLE public.user_engagement_metrics
        ADD COLUMN period_end TIMESTAMPTZ;
    END IF;

    -- Add total_responses column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'user_engagement_metrics'
        AND column_name = 'total_responses'
    ) THEN
        ALTER TABLE public.user_engagement_metrics
        ADD COLUMN total_responses INTEGER DEFAULT 0;
    END IF;

    -- Add avg_session_duration_seconds column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'user_engagement_metrics'
        AND column_name = 'avg_session_duration_seconds'
    ) THEN
        ALTER TABLE public.user_engagement_metrics
        ADD COLUMN avg_session_duration_seconds INTEGER DEFAULT 0;
    END IF;
END $$;


-- =============================================================================
-- Function 1: refresh_kpi_views()
-- =============================================================================
-- Helper function to refresh all KPI materialized views
-- Called by the scheduler hourly

CREATE OR REPLACE FUNCTION public.refresh_kpi_views()
RETURNS TABLE(view_name TEXT, status TEXT, duration_ms INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    v_duration_ms INTEGER;
BEGIN
    -- Refresh mv_agent_performance_summary
    BEGIN
        start_time := clock_timestamp();
        REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_agent_performance_summary;
        end_time := clock_timestamp();
        v_duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;

        view_name := 'mv_agent_performance_summary';
        status := 'success';
        duration_ms := v_duration_ms;
        RETURN NEXT;
    EXCEPTION WHEN OTHERS THEN
        view_name := 'mv_agent_performance_summary';
        status := 'failed: ' || SQLERRM;
        duration_ms := 0;
        RETURN NEXT;
    END;

    -- Refresh mv_connector_kpi_trends
    BEGIN
        start_time := clock_timestamp();
        REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_connector_kpi_trends;
        end_time := clock_timestamp();
        v_duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;

        view_name := 'mv_connector_kpi_trends';
        status := 'success';
        duration_ms := v_duration_ms;
        RETURN NEXT;
    EXCEPTION WHEN OTHERS THEN
        view_name := 'mv_connector_kpi_trends';
        status := 'failed: ' || SQLERRM;
        duration_ms := 0;
        RETURN NEXT;
    END;
END;
$$;

COMMENT ON FUNCTION public.refresh_kpi_views() IS
'Refreshes all KPI materialized views and returns execution status';


-- =============================================================================
-- Function 2: cleanup_old_metrics()
-- =============================================================================
-- Helper function to delete old metric data based on retention policy
-- Called by the scheduler weekly

CREATE OR REPLACE FUNCTION public.cleanup_old_metrics(
    p_connector_kpis_retention_days INTEGER DEFAULT 90,
    p_engagement_retention_days INTEGER DEFAULT 90,
    p_agent_logs_retention_days INTEGER DEFAULT 30,
    p_scheduler_logs_retention_days INTEGER DEFAULT 30
)
RETURNS TABLE(table_name TEXT, rows_deleted INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_rows_deleted INTEGER;
    v_cutoff_date DATE;
BEGIN
    -- Clean connector_kpis
    v_cutoff_date := CURRENT_DATE - p_connector_kpis_retention_days;
    DELETE FROM public.connector_kpis WHERE extracted_at::DATE < v_cutoff_date;
    GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
    table_name := 'connector_kpis';
    rows_deleted := v_rows_deleted;
    RETURN NEXT;

    -- Clean user_engagement_metrics
    v_cutoff_date := CURRENT_DATE - p_engagement_retention_days;
    DELETE FROM public.user_engagement_metrics WHERE date < v_cutoff_date;
    GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
    table_name := 'user_engagement_metrics';
    rows_deleted := v_rows_deleted;
    RETURN NEXT;

    -- Clean agent_execution_logs (if exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agent_execution_logs') THEN
        v_cutoff_date := CURRENT_DATE - p_agent_logs_retention_days;
        EXECUTE format('DELETE FROM public.agent_execution_logs WHERE executed_at::DATE < $1')
        USING v_cutoff_date;
        GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
        table_name := 'agent_execution_logs';
        rows_deleted := v_rows_deleted;
        RETURN NEXT;
    END IF;

    -- Clean scheduler_logs
    v_cutoff_date := CURRENT_DATE - p_scheduler_logs_retention_days;
    DELETE FROM public.scheduler_logs WHERE executed_at::DATE < v_cutoff_date;
    GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
    table_name := 'scheduler_logs';
    rows_deleted := v_rows_deleted;
    RETURN NEXT;
END;
$$;

COMMENT ON FUNCTION public.cleanup_old_metrics IS
'Deletes old metric data based on retention policy. Returns count of rows deleted per table.';


-- =============================================================================
-- Function 3: get_scheduler_health()
-- =============================================================================
-- Helper function to check scheduler health and view freshness

CREATE OR REPLACE FUNCTION public.get_scheduler_health()
RETURNS TABLE(
    metric_name TEXT,
    metric_value TEXT,
    is_healthy BOOLEAN
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_agent_refresh TIMESTAMPTZ;
    v_connector_refresh TIMESTAMPTZ;
    v_last_scheduler_run TIMESTAMPTZ;
    v_failed_tasks_count INTEGER;
BEGIN
    -- Check last view refresh times
    SELECT MAX(last_refreshed) INTO v_agent_refresh
    FROM public.mv_agent_performance_summary;

    metric_name := 'agent_view_last_refresh';
    metric_value := COALESCE(v_agent_refresh::TEXT, 'never');
    is_healthy := (v_agent_refresh IS NOT NULL AND v_agent_refresh > NOW() - INTERVAL '2 hours');
    RETURN NEXT;

    SELECT MAX(last_refreshed) INTO v_connector_refresh
    FROM public.mv_connector_kpi_trends;

    metric_name := 'connector_view_last_refresh';
    metric_value := COALESCE(v_connector_refresh::TEXT, 'never');
    is_healthy := (v_connector_refresh IS NOT NULL AND v_connector_refresh > NOW() - INTERVAL '2 hours');
    RETURN NEXT;

    -- Check last scheduler execution
    SELECT MAX(executed_at) INTO v_last_scheduler_run
    FROM public.scheduler_logs;

    metric_name := 'last_scheduler_execution';
    metric_value := COALESCE(v_last_scheduler_run::TEXT, 'never');
    is_healthy := (v_last_scheduler_run IS NOT NULL AND v_last_scheduler_run > NOW() - INTERVAL '2 hours');
    RETURN NEXT;

    -- Check for recent failed tasks
    SELECT COUNT(*) INTO v_failed_tasks_count
    FROM public.scheduler_logs
    WHERE status = 'failed'
    AND executed_at > NOW() - INTERVAL '24 hours';

    metric_name := 'failed_tasks_last_24h';
    metric_value := v_failed_tasks_count::TEXT;
    is_healthy := (v_failed_tasks_count = 0);
    RETURN NEXT;
END;
$$;

COMMENT ON FUNCTION public.get_scheduler_health IS
'Returns health metrics for the KPI scheduler system';


-- =============================================================================
-- Storage Bucket for KPI Reports
-- =============================================================================
-- Create storage bucket for KPI reports (run this in Supabase Dashboard or via API)
-- Note: This is a SQL comment as storage buckets are typically created via Supabase UI or API

/*
To create the storage bucket, run this in the Supabase Dashboard -> Storage:

1. Go to Storage section
2. Click "New Bucket"
3. Name: "kpi-reports"
4. Make it private (only authenticated users can access)
5. Set RLS policies as needed

Or use the Supabase API:
supabase.storage.createBucket('kpi-reports', { public: false })

RLS Policy example (run in SQL Editor):

-- Policy to allow authenticated users to read their organization's reports
CREATE POLICY "Users can read their org reports" ON storage.objects
FOR SELECT
USING (
    bucket_id = 'kpi-reports'
    AND auth.uid() IN (
        SELECT id FROM public.users
        WHERE organization_id::TEXT = (storage.foldername(name))[1]
    )
);

-- Policy to allow service role to insert reports
CREATE POLICY "Service role can insert reports" ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = 'kpi-reports');
*/


-- =============================================================================
-- Grant Permissions
-- =============================================================================
-- Ensure the service role can access these tables and functions

GRANT ALL ON public.scheduler_logs TO postgres, authenticated, service_role;
GRANT ALL ON public.kpi_reports TO postgres, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.refresh_kpi_views() TO postgres, service_role;
GRANT EXECUTE ON FUNCTION public.cleanup_old_metrics TO postgres, service_role;
GRANT EXECUTE ON FUNCTION public.get_scheduler_health() TO postgres, authenticated, service_role;


-- =============================================================================
-- Row Level Security (RLS)
-- =============================================================================
-- Enable RLS on new tables

ALTER TABLE public.scheduler_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kpi_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Service role has full access to scheduler_logs
CREATE POLICY "Service role full access to scheduler_logs" ON public.scheduler_logs
FOR ALL
USING (true)
WITH CHECK (true);

-- Policy: Users can view their organization's reports
CREATE POLICY "Users can view their org reports" ON public.kpi_reports
FOR SELECT
USING (
    organization_id IN (
        SELECT organization_id FROM public.users WHERE id = auth.uid()
    )
);

-- Policy: Service role can insert/update reports
CREATE POLICY "Service role can manage reports" ON public.kpi_reports
FOR ALL
USING (true)
WITH CHECK (true);


-- =============================================================================
-- Initial Data / Test Query
-- =============================================================================
-- Verify tables were created

DO $$
BEGIN
    RAISE NOTICE 'Migration 005 completed successfully!';
    RAISE NOTICE 'Tables created: scheduler_logs, kpi_reports';
    RAISE NOTICE 'Functions created: refresh_kpi_views(), cleanup_old_metrics(), get_scheduler_health()';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Create storage bucket "kpi-reports" in Supabase Dashboard';
    RAISE NOTICE '2. Deploy backend code with kpi_scheduler.py';
    RAISE NOTICE '3. Monitor scheduler_logs table for task execution';
    RAISE NOTICE '4. Test manual triggers via API: POST /api/kpis/scheduler/trigger/{task_name}';
END $$;


-- =============================================================================
-- Test Queries (optional, for verification)
-- =============================================================================

-- Check scheduler logs
-- SELECT * FROM public.scheduler_logs ORDER BY executed_at DESC LIMIT 10;

-- Check KPI reports
-- SELECT * FROM public.kpi_reports ORDER BY generated_at DESC LIMIT 10;

-- Test view refresh function
-- SELECT * FROM public.refresh_kpi_views();

-- Test cleanup function (dry run - won't delete data if retention is high)
-- SELECT * FROM public.cleanup_old_metrics(365, 365, 365, 365);

-- Check scheduler health
-- SELECT * FROM public.get_scheduler_health();
