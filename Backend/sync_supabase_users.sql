
--Sync Supabase Auth Users to Custom Users Table


-- Step 1: Add password_hash column if it doesn't exist
-- ============================================================================
ALTER TABLE users
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Step 2: Ensure organization exists
-- ============================================================================
INSERT INTO organizations (id, name, industry, project_number)
VALUES (1, 'Kogna Organization', 'Technology', 0)
ON CONFLICT (id) DO NOTHING;

-- Step 3: Sync Allen from auth.users to public.users
-- ============================================================================
INSERT INTO users (
    organization_id,
    first_name,
    second_name,
    role,
    email,
    password_hash,
    created_at
)
SELECT
    1 as organization_id,
    'Allen' as first_name,
    NULL as second_name,
    'founder' as role,
    email,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeshXlF7kFTEq6/D.VYMZp4Sa' as password_hash,  -- password: demo123
    created_at
FROM auth.users
WHERE email = 'allen@kognadash.com'
ON CONFLICT (email) DO UPDATE
SET
    first_name = EXCLUDED.first_name,
    role = EXCLUDED.role,
    organization_id = EXCLUDED.organization_id,
    password_hash = EXCLUDED.password_hash;

-- Step 4: Sync Sarah from auth.users to public.users
-- ============================================================================
INSERT INTO users (
    organization_id,
    first_name,
    second_name,
    role,
    email,
    password_hash,
    created_at
)
SELECT
    1 as organization_id,
    'Sarah' as first_name,
    'Chen' as second_name,
    'executive' as role,
    email,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeshXlF7kFTEq6/D.VYMZp4Sa' as password_hash,  -- password: demo123
    created_at
FROM auth.users
WHERE email = 'sarah@kognadash.com'
ON CONFLICT (email) DO UPDATE
SET
    first_name = EXCLUDED.first_name,
    second_name = EXCLUDED.second_name,
    role = EXCLUDED.role,
    organization_id = EXCLUDED.organization_id,
    password_hash = EXCLUDED.password_hash;

-- Step 5: Verify the sync
-- ============================================================================
SELECT
    id,
    email,
    first_name,
    second_name,
    role,
    organization_id,
    CASE
        WHEN password_hash IS NOT NULL THEN '✓ Password Set'
        ELSE '✗ No Password'
    END as password_status,
    created_at
FROM users
WHERE email IN ('allen@kognadash.com', 'sarah@kognadash.com')
ORDER BY email;
