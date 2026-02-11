-- ============================================================================
-- Migration 013: Create BI Embedding Framework tables
-- ============================================================================

-- 1. BI Tool connection configurations
CREATE TABLE IF NOT EXISTS bi_connectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    provider VARCHAR(50) NOT NULL,        -- tableau, powerbi, looker, superset, metabase
    display_name VARCHAR(255),

    server_url TEXT,
    site_name VARCHAR(255),
    api_key TEXT,
    api_secret TEXT,
    embed_secret TEXT,
    auth_token TEXT,
    refresh_token TEXT,
    token_expires_at BIGINT,

    -- Power BI specific
    tenant_id VARCHAR(255),
    workspace_id VARCHAR(255),

    config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'configured',  -- configured, connected, error, disconnected
    last_verified_at TIMESTAMP,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Registered dashboards for embedding
CREATE TABLE IF NOT EXISTS bi_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bi_connector_id UUID NOT NULL REFERENCES bi_connectors(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    external_dashboard_id VARCHAR(500),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    thumbnail_url TEXT,

    embed_url TEXT,
    embed_config JSONB DEFAULT '{}',

    is_default BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    allowed_team_ids UUID[] DEFAULT '{}',

    last_accessed_at TIMESTAMP,
    sort_order INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. KPI snapshots for native executive dashboard
CREATE TABLE IF NOT EXISTS executive_kpi_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    category VARCHAR(50) NOT NULL,      -- incidents, problems, requests
    kpi_name VARCHAR(100) NOT NULL,
    kpi_value NUMERIC,
    kpi_unit VARCHAR(50),

    previous_value NUMERIC,
    change_percent NUMERIC,
    trend_direction VARCHAR(10),        -- up, down, stable

    period_type VARCHAR(20) NOT NULL,   -- ytd, monthly, quarterly
    period_label VARCHAR(50),
    snapshot_date DATE NOT NULL,

    breakdown JSONB DEFAULT '{}',
    monthly_trend JSONB DEFAULT '[]',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_bi_connectors_user ON bi_connectors(user_id);
CREATE INDEX IF NOT EXISTS idx_bi_connectors_org ON bi_connectors(organization_id);
CREATE INDEX IF NOT EXISTS idx_bi_connectors_provider ON bi_connectors(provider);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bi_connectors_unique
    ON bi_connectors(user_id, organization_id, provider);

CREATE INDEX IF NOT EXISTS idx_bi_dashboards_connector ON bi_dashboards(bi_connector_id);
CREATE INDEX IF NOT EXISTS idx_bi_dashboards_org ON bi_dashboards(organization_id);

CREATE INDEX IF NOT EXISTS idx_exec_kpi_org_date
    ON executive_kpi_snapshots(organization_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_exec_kpi_category
    ON executive_kpi_snapshots(category, kpi_name);

-- ============================================================================
-- Auto-update triggers
-- ============================================================================
CREATE OR REPLACE FUNCTION update_bi_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_bi_connectors_updated_at ON bi_connectors;
CREATE TRIGGER trigger_bi_connectors_updated_at
    BEFORE UPDATE ON bi_connectors
    FOR EACH ROW EXECUTE FUNCTION update_bi_updated_at();

DROP TRIGGER IF EXISTS trigger_bi_dashboards_updated_at ON bi_dashboards;
CREATE TRIGGER trigger_bi_dashboards_updated_at
    BEFORE UPDATE ON bi_dashboards
    FOR EACH ROW EXECUTE FUNCTION update_bi_updated_at();
