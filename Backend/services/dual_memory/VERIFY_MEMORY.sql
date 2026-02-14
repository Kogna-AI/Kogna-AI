-- Verify Memory Storage - SIMPLIFIED
-- =====================================
-- Only checking the tables critical for memory test

-- 1. Check conversations stored
SELECT
    id,
    user_id,
    session_id,
    query,
    response_summary,
    created_at
FROM user_conversational_memory
ORDER BY created_at DESC
LIMIT 10;

-- 2. Check business facts stored
SELECT
    id,
    user_id,
    fact_type,
    subject,
    predicate,
    value,
    source_conversation_id,
    valid_from
FROM user_business_facts
ORDER BY valid_from DESC
LIMIT 10;

-- 3. ⭐ CRITICAL: Check risks stored (Test 2 used this!)
SELECT
    id,
    user_id,
    title,
    description,
    severity,
    category,
    source_conversation_id,
    valid_from
FROM user_risks
WHERE valid_to IS NULL  -- Active risks only
ORDER BY valid_from DESC
LIMIT 10;

-- 4. ⭐ CRITICAL: Check company context stored (Test 4 needs this!)
SELECT
    user_id,
    key,
    value,
    source_conversation_id,
    valid_from
FROM user_company_context
ORDER BY valid_from DESC
LIMIT 10;

-- 5. Count summary for test user
-- Replace '0088702d-9313-4343-8ae3-2e6f98c5af8d' with your test user_id
SELECT
    'Conversations' as type,
    COUNT(*) as count
FROM user_conversational_memory
WHERE user_id = '0088702d-9313-4343-8ae3-2e6f98c5af8d'
UNION ALL
SELECT
    'Facts' as type,
    COUNT(*) as count
FROM user_business_facts
WHERE user_id = '0088702d-9313-4343-8ae3-2e6f98c5af8d'
UNION ALL
SELECT
    'Risks' as type,
    COUNT(*) as count
FROM user_risks
WHERE user_id = '0088702d-9313-4343-8ae3-2e6f98c5af8d'
  AND valid_to IS NULL
UNION ALL
SELECT
    'Company Context' as type,
    COUNT(*) as count
FROM user_company_context
WHERE user_id = '0088702d-9313-4343-8ae3-2e6f98c5af8d';

-- 6. ⭐⭐⭐ MOST IMPORTANT: Quick view of what was stored
-- This shows both risks AND company context in one result
SELECT
    'Risk' as type,
    title as name,
    description as details,
    severity,
    valid_from
FROM user_risks
WHERE user_id = '0088702d-9313-4343-8ae3-2e6f98c5af8d'
  AND valid_to IS NULL
UNION ALL
SELECT
    'Company Info' as type,
    key as name,
    value as details,
    NULL as severity,
    valid_from
FROM user_company_context
WHERE user_id = '0088702d-9313-4343-8ae3-2e6f98c5af8d'
ORDER BY type, valid_from DESC;
