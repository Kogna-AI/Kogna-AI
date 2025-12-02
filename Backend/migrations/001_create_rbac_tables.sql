-- ============================================================================
-- RBAC (Role-Based Access Control) Database Schema
-- ============================================================================
-- This migration creates the necessary tables for the RBAC system
-- and populates them with default roles and permissions.
-- ============================================================================

-- Step 1: Create roles table
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    level INTEGER NOT NULL,  -- Hierarchy: 1=viewer, 2=analyst, 3=manager, 4=executive, 5=admin
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create permissions table
-- ============================================================================
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    resource VARCHAR(100) NOT NULL,  -- e.g., 'agents', 'insights', 'objectives'
    action VARCHAR(50) NOT NULL,     -- e.g., 'read', 'write', 'invoke'
    scope VARCHAR(50) NOT NULL,      -- e.g., 'own', 'team', 'organization'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action, scope)
);

-- Step 3: Create user_roles junction table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    UNIQUE(user_id, role_id)
);

-- Step 4: Create role_permissions junction table
-- ============================================================================
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);

-- Step 5: Create audit_logs table
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    query TEXT,
    results_count INTEGER,
    execution_time_ms INTEGER,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 6: Insert default roles
-- ============================================================================
INSERT INTO roles (name, level, description) VALUES
    ('viewer', 1, 'Can view own data and assigned information'),
    ('analyst', 2, 'Can view and analyze team data'),
    ('manager', 3, 'Can view and manage organization-wide data'),
    ('executive', 4, 'Full access to all organization data and strategic insights'),
    ('admin', 5, 'System administrator with full access')
ON CONFLICT (name) DO NOTHING;

-- Step 7: Insert default permissions
-- ============================================================================

-- Agent permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('agents', 'invoke', 'own'),
    ('agents', 'invoke', 'team'),
    ('agents', 'invoke', 'organization')
ON CONFLICT DO NOTHING;

-- Insights permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('insights', 'read', 'own'),
    ('insights', 'read', 'team'),
    ('insights', 'read', 'organization'),
    ('insights', 'write', 'own'),
    ('insights', 'write', 'organization')
ON CONFLICT DO NOTHING;

-- Objectives permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('objectives', 'read', 'own'),
    ('objectives', 'read', 'team'),
    ('objectives', 'read', 'organization'),
    ('objectives', 'write', 'own'),
    ('objectives', 'write', 'team'),
    ('objectives', 'write', 'organization')
ON CONFLICT DO NOTHING;

-- Metrics permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('metrics', 'read', 'own'),
    ('metrics', 'read', 'team'),
    ('metrics', 'read', 'organization'),
    ('metrics', 'write', 'organization')
ON CONFLICT DO NOTHING;

-- Users permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('users', 'read', 'own'),
    ('users', 'read', 'team'),
    ('users', 'read', 'organization'),
    ('users', 'write', 'own'),
    ('users', 'write', 'organization')
ON CONFLICT DO NOTHING;

-- Teams permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('teams', 'read', 'own'),
    ('teams', 'read', 'organization'),
    ('teams', 'write', 'organization')
ON CONFLICT DO NOTHING;

-- Recommendations permissions
INSERT INTO permissions (resource, action, scope) VALUES
    ('recommendations', 'read', 'own'),
    ('recommendations', 'read', 'team'),
    ('recommendations', 'read', 'organization'),
    ('recommendations', 'write', 'own'),
    ('recommendations', 'write', 'organization')
ON CONFLICT DO NOTHING;

-- Step 8: Assign permissions to roles
-- ============================================================================

-- Viewer role (level 1) - Can view own data only
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'viewer'
  AND p.scope = 'own'
ON CONFLICT DO NOTHING;

-- Analyst role (level 2) - Can view and analyze team data
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'analyst'
  AND (p.scope IN ('own', 'team'))
ON CONFLICT DO NOTHING;

-- Manager role (level 3) - Can view and manage organization data
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'manager'
  AND p.resource IN ('insights', 'objectives', 'metrics', 'users', 'teams', 'recommendations')
ON CONFLICT DO NOTHING;

-- Executive role (level 4) - Full access
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'executive'
ON CONFLICT DO NOTHING;

-- Admin role (level 5) - Full system access
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Step 9: Assign default roles to existing users
-- ============================================================================
-- Assign executive role to all users with 'executive' in their role column
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN roles r
WHERE u.role ILIKE '%executive%'
  AND r.name = 'executive'
ON CONFLICT DO NOTHING;

-- Assign manager role to users with 'manager' in their role column
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN roles r
WHERE u.role ILIKE '%manager%'
  AND r.name = 'manager'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
  )
ON CONFLICT DO NOTHING;

-- Assign analyst role to users with 'analyst' in their role column
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN roles r
WHERE u.role ILIKE '%analyst%'
  AND r.name = 'analyst'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
  )
ON CONFLICT DO NOTHING;

-- Assign viewer role to all other users without a role assigned
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN roles r
WHERE r.name = 'viewer'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
  )
ON CONFLICT DO NOTHING;

-- Step 10: Create indexes for better performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Step 11: Verify the setup
-- ============================================================================
SELECT 'RBAC Tables Created Successfully!' as status;

SELECT
    'Roles: ' || COUNT(*)::text as summary
FROM roles
UNION ALL
SELECT
    'Permissions: ' || COUNT(*)::text
FROM permissions
UNION ALL
SELECT
    'User Roles Assigned: ' || COUNT(*)::text
FROM user_roles
UNION ALL
SELECT
    'Role Permissions Assigned: ' || COUNT(*)::text
FROM role_permissions;
