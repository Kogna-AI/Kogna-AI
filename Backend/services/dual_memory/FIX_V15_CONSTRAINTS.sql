-- ============================================================================
-- Fix Kogna V1.5 Constraint Issues
-- ============================================================================
-- Run this to fix remaining foreign key and unique constraints that block TMS
-- ============================================================================

-- 1. Drop FK constraint from fact_conflicts table (allows test users)
ALTER TABLE fact_conflicts
DROP CONSTRAINT IF EXISTS fact_conflicts_user_id_fkey;

-- 2. Drop unique constraint from user_company_context to allow conflict detection
-- (We need to TEMPORARILY allow duplicates so TMS can detect conflicts before deduping)
ALTER TABLE user_company_context
DROP CONSTRAINT IF EXISTS unique_context_per_user;

-- 3. Add a conditional unique constraint that allows NULL valid_to (active rows only)
-- This allows historical rows (valid_to IS NOT NULL) to coexist with active row
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_context_per_user
ON user_company_context(user_id, key)
WHERE valid_to IS NULL;

-- ============================================================================
-- Verification
-- ============================================================================

-- Check that constraints were dropped
SELECT
    conname as constraint_name,
    conrelid::regclass as table_name
FROM pg_constraint
WHERE conname IN ('fact_conflicts_user_id_fkey', 'unique_context_per_user');

-- Should return 0 rows if successful
