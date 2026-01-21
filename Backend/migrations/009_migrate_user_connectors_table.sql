-- ============================================================================
-- Phase 1: Migrate user_connectors table for RBAC
-- ============================================================================
-- This migration ensures the user_connectors table exists in the database
-- (it may currently only exist in Supabase) and adds organization_id and team_id
-- columns for proper multi-tenant isolation.
--
-- The user_connectors table stores OAuth tokens and connector metadata for
-- integrated services (Jira, Google Drive, Microsoft, etc.)
-- ============================================================================

-- ============================================================================
-- Part 1: Create user_connectors table if it doesn't exist
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_connectors (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    service VARCHAR(100) NOT NULL,      -- jira, google_drive, microsoft_excel, asana, slack, github, notion
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at BIGINT,
    scope TEXT,                         -- OAuth scopes granted
    metadata JSONB,                     -- Additional connector-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Part 2: Add organization_id and team_id columns if table already exists
-- ============================================================================

-- Add organization_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'organization_id'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add team_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'team_id'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN team_id UUID REFERENCES teams(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add created_at if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add updated_at if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add service if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'service'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN service VARCHAR(100) NOT NULL DEFAULT 'unknown';
    END IF;
END $$;

-- Add access_token if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'access_token'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN access_token TEXT;
    END IF;
END $$;

-- Add refresh_token if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'refresh_token'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN refresh_token TEXT;
    END IF;
END $$;

-- Add expires_at if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN expires_at BIGINT;
    END IF;
END $$;

-- Add scope if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'scope'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN scope TEXT;
    END IF;
END $$;

-- Add metadata if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_connectors'
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE user_connectors
        ADD COLUMN metadata JSONB;
    END IF;
END $$;

-- ============================================================================
-- Part 3: Create indexes for performance
-- ============================================================================

-- Index on user_id for fast user lookup
CREATE INDEX IF NOT EXISTS idx_user_connectors_user_id ON user_connectors(user_id);

-- Index on organization_id for organization-level queries
CREATE INDEX IF NOT EXISTS idx_user_connectors_organization_id ON user_connectors(organization_id);

-- Index on team_id for team-level queries
CREATE INDEX IF NOT EXISTS idx_user_connectors_team_id ON user_connectors(team_id);

-- Index on service for connector type filtering
CREATE INDEX IF NOT EXISTS idx_user_connectors_service ON user_connectors(service);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_user_connectors_org_team_service
ON user_connectors(organization_id, team_id, service);

-- ============================================================================
-- Part 4: Add unique constraint
-- ============================================================================

-- Each user can have only one connector per organization per service
-- Drop old constraint if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_connectors_user_id_service_key'
    ) THEN
        ALTER TABLE user_connectors
        DROP CONSTRAINT user_connectors_user_id_service_key;
    END IF;
END $$;

-- Drop existing unique index if it exists (in case of re-run)
DROP INDEX IF EXISTS idx_user_connectors_unique;
DROP INDEX IF EXISTS idx_user_connectors_unique_no_org;

-- Before creating unique constraint, we need to remove duplicates
-- This is safe because we're keeping the most recent record
DO $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Remove duplicates, keeping only the most recent record per (user_id, organization_id, service)
    DELETE FROM user_connectors
    WHERE id IN (
        SELECT id
        FROM (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, COALESCE(organization_id, '00000000-0000-0000-0000-000000000000'::UUID), service
                    ORDER BY
                        COALESCE(created_at, CURRENT_TIMESTAMP) DESC,
                        id DESC
                ) as rn
            FROM user_connectors
        ) ranked
        WHERE rn > 1
    );

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    IF v_deleted_count > 0 THEN
        RAISE NOTICE 'Removed % duplicate user_connectors records', v_deleted_count;
    END IF;
END $$;

-- Add new unique constraint with organization_id (partial index for non-null org_id)
CREATE UNIQUE INDEX idx_user_connectors_unique
ON user_connectors(user_id, organization_id, service)
WHERE organization_id IS NOT NULL;

-- For records without organization_id, use a different constraint
CREATE UNIQUE INDEX idx_user_connectors_unique_no_org
ON user_connectors(user_id, service)
WHERE organization_id IS NULL;

-- ============================================================================
-- Part 5: Add updated_at trigger
-- ============================================================================

-- Create trigger function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_connectors_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if it exists
DROP TRIGGER IF EXISTS trigger_user_connectors_updated_at ON user_connectors;

-- Create trigger
CREATE TRIGGER trigger_user_connectors_updated_at
    BEFORE UPDATE ON user_connectors
    FOR EACH ROW
    EXECUTE FUNCTION update_user_connectors_updated_at();

-- ============================================================================
-- Part 6: Backfill organization_id from users table
-- ============================================================================

-- For existing records, backfill organization_id from users table
UPDATE user_connectors uc
SET organization_id = u.organization_id
FROM users u
WHERE uc.user_id = u.id
    AND uc.organization_id IS NULL;

-- ============================================================================
-- Part 7: Make organization_id NOT NULL after backfill
-- ============================================================================

-- Now that existing records are backfilled, make organization_id required
-- for new records (but keep it nullable for backward compatibility if needed)
-- Uncomment the following lines if you want to enforce NOT NULL:
-- ALTER TABLE user_connectors
-- ALTER COLUMN organization_id SET NOT NULL;

-- ============================================================================
-- Part 8: Add comments for documentation
-- ============================================================================

COMMENT ON TABLE user_connectors IS 'Stores OAuth connector credentials and metadata for integrated services';
COMMENT ON COLUMN user_connectors.user_id IS 'User who owns this connector';
COMMENT ON COLUMN user_connectors.organization_id IS 'Organization the connector belongs to';
COMMENT ON COLUMN user_connectors.team_id IS 'Team the connector is associated with (nullable)';
COMMENT ON COLUMN user_connectors.service IS 'Service type: jira, google_drive, microsoft_excel, asana, slack, github, notion';
COMMENT ON COLUMN user_connectors.access_token IS 'OAuth access token (encrypted in production)';
COMMENT ON COLUMN user_connectors.refresh_token IS 'OAuth refresh token (encrypted in production)';
COMMENT ON COLUMN user_connectors.expires_at IS 'Unix timestamp when access token expires';
COMMENT ON COLUMN user_connectors.scope IS 'OAuth scopes granted by user';
COMMENT ON COLUMN user_connectors.metadata IS 'Additional connector-specific configuration and data';

-- ============================================================================
-- Part 9: Verification
-- ============================================================================

SELECT 'user_connectors table migration completed successfully!' as status;

-- Verify table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'user_connectors'
    AND column_name IN ('user_id', 'organization_id', 'team_id', 'service', 'access_token')
ORDER BY ordinal_position;

-- Verify indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'user_connectors'
ORDER BY indexname;

-- Check row count
SELECT
    COUNT(*) as total_connectors,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT organization_id) as unique_organizations,
    COUNT(DISTINCT team_id) as unique_teams,
    COUNT(*) FILTER (WHERE organization_id IS NULL) as missing_org_id,
    COUNT(*) FILTER (WHERE team_id IS NULL) as missing_team_id
FROM user_connectors;
