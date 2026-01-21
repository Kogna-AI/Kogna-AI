-- ============================================================================
-- Cleanup: Remove duplicate records from user_connectors
-- ============================================================================
-- This migration identifies and removes duplicate entries in user_connectors
-- before applying the unique constraint.
--
-- Strategy: Keep the most recent record (based on created_at or id) and
-- delete older duplicates.
-- ============================================================================

-- ============================================================================
-- Part 1: Identify duplicates
-- ============================================================================

-- Show duplicate records before cleanup
SELECT
    'Duplicate records found:' as status;

SELECT
    user_id,
    organization_id,
    service,
    COUNT(*) as duplicate_count,
    ARRAY_AGG(id ORDER BY created_at DESC NULLS LAST, id DESC) as record_ids
FROM user_connectors
WHERE organization_id IS NOT NULL  -- Only check records with organization_id
GROUP BY user_id, organization_id, service
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- ============================================================================
-- Part 2: Create backup table (optional but recommended)
-- ============================================================================

-- Create a backup of user_connectors before deletion
CREATE TABLE IF NOT EXISTS user_connectors_backup AS
SELECT * FROM user_connectors WHERE 1=0;  -- Create empty table with same structure

-- Insert all records into backup
INSERT INTO user_connectors_backup
SELECT * FROM user_connectors
ON CONFLICT DO NOTHING;

SELECT
    'Backup created with ' || COUNT(*) || ' records' as backup_status
FROM user_connectors_backup;

-- ============================================================================
-- Part 3: Remove duplicates - Keep most recent record
-- ============================================================================

-- Delete duplicate records, keeping only the most recent one
-- (based on created_at DESC, then id DESC)
DELETE FROM user_connectors
WHERE id IN (
    SELECT id
    FROM (
        SELECT
            id,
            ROW_NUMBER() OVER (
                PARTITION BY user_id, COALESCE(organization_id, '00000000-0000-0000-0000-000000000000'::UUID), service
                ORDER BY
                    created_at DESC NULLS LAST,
                    id DESC
            ) as rn
        FROM user_connectors
    ) ranked
    WHERE rn > 1  -- Keep only the first (most recent) record
);

-- ============================================================================
-- Part 4: Verification
-- ============================================================================

-- Verify no duplicates remain
SELECT
    'Remaining duplicates (should be 0):' as status;

SELECT
    user_id,
    organization_id,
    service,
    COUNT(*) as count
FROM user_connectors
WHERE organization_id IS NOT NULL
GROUP BY user_id, organization_id, service
HAVING COUNT(*) > 1;

-- Show summary statistics
SELECT
    'Cleanup summary:' as status;

SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT organization_id) as unique_organizations,
    COUNT(DISTINCT service) as unique_services,
    COUNT(*) FILTER (WHERE organization_id IS NULL) as missing_org_id
FROM user_connectors;

-- ============================================================================
-- Part 5: Now safe to create unique constraint
-- ============================================================================

-- Drop existing index if it exists
DROP INDEX IF EXISTS idx_user_connectors_unique;

-- Create the unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_connectors_unique
ON user_connectors(user_id, organization_id, service)
WHERE organization_id IS NOT NULL;  -- Partial index: only enforce when org_id is present

-- For records without organization_id, use a different constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_connectors_unique_no_org
ON user_connectors(user_id, service)
WHERE organization_id IS NULL;

SELECT 'Unique constraints created successfully!' as status;
