-- ============================================================================
-- KPI Extraction System - Extend Existing Tables
-- ============================================================================
-- This migration extends existing tables (agent_traces and sync_jobs) with
-- additional columns for performance tracking and KPI extraction metrics.
-- ============================================================================

-- ============================================================================
-- Part 1: Create agent_traces table if it doesn't exist
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_traces (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID,
    message_id UUID,
    agent_name VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add base columns if table already exists without them
ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS session_id UUID;

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS message_id UUID;

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS agent_name VARCHAR(100);

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS input_data JSONB;

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS output_data JSONB;

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS metadata JSONB;

ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ============================================================================
-- Part 2: Extend agent_traces table with new columns
-- ============================================================================
-- Add execution_time_ms column
ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER CHECK (execution_time_ms >= 0);

-- Add token_count column
ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT 0 CHECK (token_count >= 0);

-- Add model_used column
ALTER TABLE agent_traces
ADD COLUMN IF NOT EXISTS model_used VARCHAR(100);

-- ============================================================================
-- Part 3: Create sync_jobs table if it doesn't exist
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    connector_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    items_processed INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add base columns if table already exists without them
ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS connector_type VARCHAR(100);

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS status VARCHAR(50);

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS items_processed INTEGER DEFAULT 0;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS items_failed INTEGER DEFAULT 0;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS metadata JSONB;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ============================================================================
-- Part 4: Extend sync_jobs table with new columns
-- ============================================================================
-- Add kpis_extracted column
ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS kpis_extracted INTEGER DEFAULT 0 CHECK (kpis_extracted >= 0);

-- Add kpi_extraction_time_ms column
ALTER TABLE sync_jobs
ADD COLUMN IF NOT EXISTS kpi_extraction_time_ms INTEGER CHECK (kpi_extraction_time_ms >= 0);

-- ============================================================================
-- Part 5: Create indexes for new columns
-- ============================================================================
-- Indexes for agent_traces
CREATE INDEX IF NOT EXISTS idx_agent_traces_user_id ON agent_traces(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_traces_organization_id ON agent_traces(organization_id);
CREATE INDEX IF NOT EXISTS idx_agent_traces_session_id ON agent_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_traces_agent_name ON agent_traces(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_traces_created_at ON agent_traces(created_at);

-- Indexes for sync_jobs
CREATE INDEX IF NOT EXISTS idx_sync_jobs_user_id ON sync_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_organization_id ON sync_jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_connector_type ON sync_jobs(connector_type);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON sync_jobs(status);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_created_at ON sync_jobs(created_at);

-- ============================================================================
-- Part 6: Verification
-- ============================================================================
SELECT 'Existing Tables Extended Successfully!' as status;

SELECT
    'agent_traces: Extended with execution_time_ms, token_count, model_used' as table_status
UNION ALL
SELECT
    'sync_jobs: Extended with kpis_extracted, kpi_extraction_time_ms';
