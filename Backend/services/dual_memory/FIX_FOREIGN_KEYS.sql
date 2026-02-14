-- Remove Foreign Key Constraints from Memory Tables
-- ===================================================
-- Run this in Supabase SQL Editor to allow memory system to work independently

-- 1. Drop FK constraint from user_conversational_memory
ALTER TABLE user_conversational_memory
DROP CONSTRAINT IF EXISTS user_conversational_memory_user_id_fkey;

-- 2. Drop FK constraint from user_business_facts
ALTER TABLE user_business_facts
DROP CONSTRAINT IF EXISTS user_business_facts_user_id_fkey;

-- 3. Drop FK constraint from user_risks
ALTER TABLE user_risks
DROP CONSTRAINT IF EXISTS user_risks_user_id_fkey;

-- 4. Drop FK constraint from user_metric_definitions
ALTER TABLE user_metric_definitions
DROP CONSTRAINT IF EXISTS user_metric_definitions_user_id_fkey;

-- 5. Drop FK constraint from user_preferences
ALTER TABLE user_preferences
DROP CONSTRAINT IF EXISTS user_preferences_user_id_fkey;

-- 6. Drop FK constraint from user_company_context
ALTER TABLE user_company_context
DROP CONSTRAINT IF EXISTS user_company_context_user_id_fkey;

-- ===================================================
-- ADDITIONAL: Remove source_conversation_id FKs
-- ===================================================
-- These cause timing issues when facts are stored before conversations

-- 7. Drop source_conversation_id FK from user_business_facts
ALTER TABLE user_business_facts
DROP CONSTRAINT IF EXISTS user_business_facts_source_conversation_id_fkey;

-- 8. Drop source_conversation_id FK from user_risks
ALTER TABLE user_risks
DROP CONSTRAINT IF EXISTS user_risks_source_conversation_id_fkey;

-- 9. Drop source_conversation_id FK from user_metric_definitions
ALTER TABLE user_metric_definitions
DROP CONSTRAINT IF EXISTS user_metric_definitions_source_conversation_id_fkey;

-- 10. Drop source_conversation_id FK from user_company_context
ALTER TABLE user_company_context
DROP CONSTRAINT IF EXISTS user_company_context_source_conversation_id_fkey;

-- Verification Query
-- ===================
-- Check that all constraints are removed (should return 0 rows)
SELECT
    conname as constraint_name,
    conrelid::regclass as table_name
FROM pg_constraint
WHERE (conname LIKE '%user_id_fkey' OR conname LIKE '%source_conversation_id_fkey')
  AND conrelid::regclass::text IN (
    'user_conversational_memory',
    'user_business_facts',
    'user_risks',
    'user_metric_definitions',
    'user_preferences',
    'user_company_context'
  );
