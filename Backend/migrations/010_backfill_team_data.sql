-- ============================================================================
-- Phase 1: Backfill team_id for existing KPI records
-- ============================================================================
-- This migration backfills team_id for all existing KPI-related records based
-- on the user's team membership at the time of creation.
--
-- Strategy:
-- - Use user's PRIMARY team from team_members table
-- - If user has no team or is not in team_members, leave team_id as NULL
-- - This is safe because team_id is nullable by design
--
-- Tables Updated:
-- - connector_kpis
-- - agent_performance_metrics
-- - user_engagement_metrics
-- - rag_quality_metrics
-- - sync_jobs
-- - user_connectors
-- ============================================================================

-- ============================================================================
-- Part 1: Create helper function to get user's primary team
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_primary_team(p_user_id UUID)
RETURNS UUID AS $$
DECLARE
    v_team_id UUID;
BEGIN
    -- Get the most recent team the user joined
    SELECT team_id INTO v_team_id
    FROM team_members
    WHERE user_id = p_user_id
    ORDER BY created_at DESC
    LIMIT 1;

    RETURN v_team_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 2: Backfill connector_kpis
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE connector_kpis
    SET team_id = get_user_primary_team(user_id)
    WHERE team_id IS NULL;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'connector_kpis: Backfilled % records with team_id', v_updated_count;
END $$;

-- ============================================================================
-- Part 3: Backfill agent_performance_metrics
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE agent_performance_metrics
    SET team_id = get_user_primary_team(user_id)
    WHERE team_id IS NULL;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'agent_performance_metrics: Backfilled % records with team_id', v_updated_count;
END $$;

-- ============================================================================
-- Part 4: Backfill user_engagement_metrics
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE user_engagement_metrics
    SET team_id = get_user_primary_team(user_id)
    WHERE team_id IS NULL;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'user_engagement_metrics: Backfilled % records with team_id', v_updated_count;
END $$;

-- ============================================================================
-- Part 5: Backfill rag_quality_metrics (organization_id and team_id)
-- ============================================================================

-- First backfill organization_id from users table
DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE rag_quality_metrics rq
    SET organization_id = u.organization_id
    FROM users u
    WHERE rq.user_id = u.id
        AND rq.organization_id IS NULL;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'rag_quality_metrics: Backfilled % records with organization_id', v_updated_count;
END $$;

-- Then backfill team_id
DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE rag_quality_metrics
    SET team_id = get_user_primary_team(user_id)
    WHERE team_id IS NULL;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'rag_quality_metrics: Backfilled % records with team_id', v_updated_count;
END $$;

-- ============================================================================
-- Part 6: Backfill sync_jobs (if table exists)
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sync_jobs') THEN
        UPDATE sync_jobs
        SET team_id = get_user_primary_team(user_id)
        WHERE team_id IS NULL;

        GET DIAGNOSTICS v_updated_count = ROW_COUNT;
        RAISE NOTICE 'sync_jobs: Backfilled % records with team_id', v_updated_count;
    ELSE
        RAISE NOTICE 'sync_jobs: Table does not exist, skipping backfill';
    END IF;
END $$;

-- ============================================================================
-- Part 7: Backfill user_connectors
-- ============================================================================

-- Backfill team_id for user_connectors
DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE user_connectors
    SET team_id = get_user_primary_team(user_id)
    WHERE team_id IS NULL;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RAISE NOTICE 'user_connectors: Backfilled % records with team_id', v_updated_count;
END $$;

-- ============================================================================
-- Part 8: Backfill audit_logs (if table exists and has team_id column)
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'audit_logs'
            AND column_name = 'team_id'
    ) THEN
        UPDATE audit_logs
        SET team_id = get_user_primary_team(user_id)
        WHERE team_id IS NULL
            AND user_id IS NOT NULL;

        GET DIAGNOSTICS v_updated_count = ROW_COUNT;
        RAISE NOTICE 'audit_logs: Backfilled % records with team_id', v_updated_count;
    ELSE
        RAISE NOTICE 'audit_logs: team_id column does not exist, skipping backfill';
    END IF;
END $$;

-- ============================================================================
-- Part 9: Refresh materialized views with new data
-- ============================================================================

-- Refresh the materialized views to include the new team_id data
-- Note: Using non-CONCURRENT refresh since views might be empty or lack unique indexes
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_matviews
        WHERE matviewname = 'mv_agent_performance_summary'
    ) THEN
        REFRESH MATERIALIZED VIEW mv_agent_performance_summary;
        RAISE NOTICE 'Refreshed mv_agent_performance_summary';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_matviews
        WHERE matviewname = 'mv_connector_kpi_trends'
    ) THEN
        REFRESH MATERIALIZED VIEW mv_connector_kpi_trends;
        RAISE NOTICE 'Refreshed mv_connector_kpi_trends';
    END IF;
END $$;

-- ============================================================================
-- Part 10: Generate backfill report
-- ============================================================================

-- Report on backfill results
SELECT 'Team data backfill completed!' as status;

-- Summary statistics
SELECT
    'connector_kpis' as table_name,
    COUNT(*) as total_records,
    COUNT(team_id) as records_with_team,
    COUNT(*) FILTER (WHERE team_id IS NULL) as records_without_team,
    ROUND(COUNT(team_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as team_coverage_percent
FROM connector_kpis

UNION ALL

SELECT
    'agent_performance_metrics',
    COUNT(*),
    COUNT(team_id),
    COUNT(*) FILTER (WHERE team_id IS NULL),
    ROUND(COUNT(team_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2)
FROM agent_performance_metrics

UNION ALL

SELECT
    'user_engagement_metrics',
    COUNT(*),
    COUNT(team_id),
    COUNT(*) FILTER (WHERE team_id IS NULL),
    ROUND(COUNT(team_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2)
FROM user_engagement_metrics

UNION ALL

SELECT
    'rag_quality_metrics',
    COUNT(*),
    COUNT(team_id),
    COUNT(*) FILTER (WHERE team_id IS NULL),
    ROUND(COUNT(team_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2)
FROM rag_quality_metrics

UNION ALL

SELECT
    'user_connectors',
    COUNT(*),
    COUNT(team_id),
    COUNT(*) FILTER (WHERE team_id IS NULL),
    ROUND(COUNT(team_id)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2)
FROM user_connectors;

-- Show distribution of records by team
SELECT
    'Records by team distribution' as report_section;

SELECT
    COALESCE(t.name, 'No Team') as team_name,
    COUNT(DISTINCT ck.id) as connector_kpis,
    COUNT(DISTINCT apm.id) as agent_metrics,
    COUNT(DISTINCT uem.id) as engagement_metrics,
    COUNT(DISTINCT rq.id) as rag_metrics,
    COUNT(DISTINCT uc.id) as user_connectors
FROM teams t
LEFT JOIN connector_kpis ck ON t.id = ck.team_id
LEFT JOIN agent_performance_metrics apm ON t.id = apm.team_id
LEFT JOIN user_engagement_metrics uem ON t.id = uem.team_id
LEFT JOIN rag_quality_metrics rq ON t.id = rq.team_id
LEFT JOIN user_connectors uc ON t.id = uc.team_id
GROUP BY t.id, t.name
ORDER BY connector_kpis DESC
LIMIT 20;

-- ============================================================================
-- Part 11: Cleanup
-- ============================================================================

-- Optionally drop the helper function if not needed
-- Uncomment the following line to drop it:
-- DROP FUNCTION IF EXISTS get_user_primary_team(UUID);

-- Keep the function for now as it might be useful for future backfills
COMMENT ON FUNCTION get_user_primary_team(UUID) IS 'Helper function to get user''s primary team ID for backfill operations';
