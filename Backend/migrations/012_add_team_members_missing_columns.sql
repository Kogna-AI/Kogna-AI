-- ============================================================================
-- Add Missing Columns to team_members Table
-- ============================================================================
-- This migration adds the is_primary and joined_at columns that are required
-- by the auth layer (dependencies.py, team_access.py) but were missing from
-- the original team_members table creation.
--
-- IMPORTANT: Run this migration BEFORE migrations 010 and 011!
-- This migration must run first because:
-- - 010_backfill_team_data.sql depends on team_members.created_at
-- - 011_fix_materialized_views_with_team.sql depends on proper team setup
--
-- Tables Modified:
-- - teams (documented if exists, created if not)
-- - team_members (add missing columns)
--
-- Columns Added to team_members:
-- - is_primary BOOLEAN: Indicates if this is the user's primary team
-- - joined_at TIMESTAMP: When the user joined the team
-- - created_at TIMESTAMP: Standard audit column (if missing)
-- - role VARCHAR(50): Team-level role (member, admin, etc.)
-- ============================================================================

-- ============================================================================
-- Part 0: Ensure teams table exists with proper structure
-- ============================================================================

-- Create teams table if it doesn't exist (it likely already exists)
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, name)
);

-- Create index on organization_id for teams
CREATE INDEX IF NOT EXISTS idx_teams_organization_id ON teams(organization_id);

-- Create team_members table if it doesn't exist
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(team_id, user_id)
);

-- Create basic indexes for team_members
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);

-- ============================================================================
-- Part 1: Add missing columns to team_members
-- ============================================================================

-- Add is_primary column (required by auth layer)
ALTER TABLE team_members
ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;

-- Add joined_at column (used for ordering in auth layer)
ALTER TABLE team_members
ADD COLUMN IF NOT EXISTS joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add created_at column (standard audit column)
ALTER TABLE team_members
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add role column if missing (for team-level roles)
ALTER TABLE team_members
ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'member';

-- ============================================================================
-- Part 2: Backfill joined_at from created_at for existing records
-- ============================================================================

UPDATE team_members
SET joined_at = COALESCE(created_at, CURRENT_TIMESTAMP)
WHERE joined_at IS NULL;

-- ============================================================================
-- Part 3: Set default primary team for each user
-- ============================================================================

-- For users without a primary team, set their earliest joined team as primary
-- This ensures each user has exactly one primary team

WITH earliest_teams AS (
    SELECT DISTINCT ON (user_id)
        id,
        user_id,
        team_id
    FROM team_members
    WHERE user_id NOT IN (
        SELECT user_id FROM team_members WHERE is_primary = TRUE
    )
    ORDER BY user_id, joined_at ASC, created_at ASC, id ASC
)
UPDATE team_members tm
SET is_primary = TRUE
FROM earliest_teams et
WHERE tm.id = et.id;

-- ============================================================================
-- Part 4: Create indexes for performance
-- ============================================================================

-- Index for finding primary team quickly
CREATE INDEX IF NOT EXISTS idx_team_members_user_primary
ON team_members(user_id, is_primary)
WHERE is_primary = TRUE;

-- Index for ordering by joined_at
CREATE INDEX IF NOT EXISTS idx_team_members_user_joined
ON team_members(user_id, joined_at);

-- Composite index for common auth queries
CREATE INDEX IF NOT EXISTS idx_team_members_user_team
ON team_members(user_id, team_id);

-- ============================================================================
-- Part 5: Add constraint to ensure only one primary per user (optional)
-- ============================================================================

-- Note: This partial unique index ensures each user can have at most one
-- primary team. However, it allows users to have no primary team.
-- Uncomment if you want to enforce this constraint:

-- CREATE UNIQUE INDEX IF NOT EXISTS idx_team_members_one_primary_per_user
-- ON team_members(user_id)
-- WHERE is_primary = TRUE;

-- ============================================================================
-- Part 6: Update the backfill helper function
-- ============================================================================

-- Update get_user_primary_team to use is_primary instead of just created_at
CREATE OR REPLACE FUNCTION get_user_primary_team(p_user_id UUID)
RETURNS UUID AS $$
DECLARE
    v_team_id UUID;
BEGIN
    -- First try to get the primary team
    SELECT team_id INTO v_team_id
    FROM team_members
    WHERE user_id = p_user_id
      AND is_primary = TRUE
    LIMIT 1;

    -- If no primary team, fall back to earliest joined team
    IF v_team_id IS NULL THEN
        SELECT team_id INTO v_team_id
        FROM team_members
        WHERE user_id = p_user_id
        ORDER BY joined_at ASC, created_at ASC
        LIMIT 1;
    END IF;

    RETURN v_team_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_primary_team(UUID) IS
'Returns user''s primary team ID. Falls back to earliest joined team if no primary set.';

-- ============================================================================
-- Part 7: Verification
-- ============================================================================

SELECT 'team_members columns added successfully!' as status;

-- Verify columns exist
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'team_members'
    AND column_name IN ('is_primary', 'joined_at', 'created_at', 'role')
ORDER BY column_name;

-- Check primary team distribution
SELECT
    'Users with primary team' as metric,
    COUNT(DISTINCT user_id) as count
FROM team_members
WHERE is_primary = TRUE

UNION ALL

SELECT
    'Users without primary team',
    COUNT(DISTINCT tm.user_id)
FROM team_members tm
WHERE NOT EXISTS (
    SELECT 1 FROM team_members tm2
    WHERE tm2.user_id = tm.user_id AND tm2.is_primary = TRUE
)

UNION ALL

SELECT
    'Total team memberships',
    COUNT(*)
FROM team_members;

-- ============================================================================
-- End of Migration
-- ============================================================================
