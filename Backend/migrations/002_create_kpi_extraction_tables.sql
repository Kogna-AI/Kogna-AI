-- ============================================================================
-- KPI Extraction System - Phase 1: Database Schema
-- ============================================================================
-- This migration creates tables and views for the KPI extraction and
-- analytics system, including agent performance tracking, connector KPIs,
-- user engagement metrics, and RAG quality monitoring.
-- ============================================================================

-- ============================================================================
-- Part 1: Create New Tables
-- ============================================================================

-- Table 1: agent_performance_metrics
-- Purpose: Track each AI agent execution performance
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    session_id UUID,
    message_id UUID,
    agent_name VARCHAR(100) NOT NULL CHECK (agent_name IN ('triage', 'internal_analyst', 'researcher', 'synthesizer', 'communicator')),
    response_time_ms INTEGER NOT NULL CHECK (response_time_ms >= 0),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    token_count INTEGER DEFAULT 0 CHECK (token_count >= 0),
    prompt_tokens INTEGER DEFAULT 0 CHECK (prompt_tokens >= 0),
    completion_tokens INTEGER DEFAULT 0 CHECK (completion_tokens >= 0),
    estimated_cost_usd DECIMAL(10, 6) DEFAULT 0.0 CHECK (estimated_cost_usd >= 0),
    model_used VARCHAR(100),
    success BOOLEAN NOT NULL DEFAULT true,
    error_type VARCHAR(255),
    confidence_score DECIMAL(5, 4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: connector_kpis
-- Purpose: Store business KPIs extracted from connectors
-- ============================================================================
CREATE TABLE IF NOT EXISTS connector_kpis (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    sync_job_id UUID,
    connector_type VARCHAR(100) NOT NULL CHECK (connector_type IN ('jira', 'google_drive', 'microsoft_excel', 'asana', 'slack', 'github', 'notion')),
    source_id VARCHAR(255) NOT NULL,
    source_name VARCHAR(500),
    kpi_category VARCHAR(100) NOT NULL CHECK (kpi_category IN ('velocity', 'burndown', 'completion_rate', 'financial', 'productivity', 'quality', 'collaboration')),
    kpi_name VARCHAR(255) NOT NULL,
    kpi_value JSONB NOT NULL,
    kpi_unit VARCHAR(100),
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, connector_type, source_id, kpi_name, period_start)
);

-- Table 3: user_engagement_metrics
-- Purpose: Track daily user interaction patterns
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_engagement_metrics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    session_count INTEGER DEFAULT 0 CHECK (session_count >= 0),
    total_session_duration_seconds INTEGER DEFAULT 0 CHECK (total_session_duration_seconds >= 0),
    query_count INTEGER DEFAULT 0 CHECK (query_count >= 0),
    avg_queries_per_session DECIMAL(10, 2) DEFAULT 0.0 CHECK (avg_queries_per_session >= 0),
    feedback_count INTEGER DEFAULT 0 CHECK (feedback_count >= 0),
    avg_satisfaction_score DECIMAL(5, 4) CHECK (avg_satisfaction_score >= 0 AND avg_satisfaction_score <= 5),
    recommendations_viewed INTEGER DEFAULT 0 CHECK (recommendations_viewed >= 0),
    recommendations_accepted INTEGER DEFAULT 0 CHECK (recommendations_accepted >= 0),
    common_topics JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, date)
);

-- Table 4: rag_quality_metrics
-- Purpose: Track RAG system quality per query
-- ============================================================================
CREATE TABLE IF NOT EXISTS rag_quality_metrics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID,
    retrieval_count INTEGER DEFAULT 0 CHECK (retrieval_count >= 0),
    avg_similarity_score DECIMAL(5, 4) CHECK (avg_similarity_score >= 0 AND avg_similarity_score <= 1),
    sources_used JSONB DEFAULT '[]'::jsonb,
    user_satisfaction INTEGER CHECK (user_satisfaction >= 1 AND user_satisfaction <= 5),
    citation_accuracy DECIMAL(5, 4) CHECK (citation_accuracy >= 0 AND citation_accuracy <= 1),
    answer_relevance DECIMAL(5, 4) CHECK (answer_relevance >= 0 AND answer_relevance <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Part 2: Create Indexes for Performance
-- ============================================================================

-- Indexes for agent_performance_metrics
CREATE INDEX IF NOT EXISTS idx_agent_performance_user_id ON agent_performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_organization_id ON agent_performance_metrics(organization_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_name ON agent_performance_metrics(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_performance_created_at ON agent_performance_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_performance_session_id ON agent_performance_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_success ON agent_performance_metrics(success);

-- Indexes for connector_kpis
CREATE INDEX IF NOT EXISTS idx_connector_kpis_user_id ON connector_kpis(user_id);
CREATE INDEX IF NOT EXISTS idx_connector_kpis_organization_id ON connector_kpis(organization_id);
CREATE INDEX IF NOT EXISTS idx_connector_kpis_connector_type ON connector_kpis(connector_type);
CREATE INDEX IF NOT EXISTS idx_connector_kpis_kpi_category ON connector_kpis(kpi_category);
CREATE INDEX IF NOT EXISTS idx_connector_kpis_extracted_at ON connector_kpis(extracted_at);
CREATE INDEX IF NOT EXISTS idx_connector_kpis_period ON connector_kpis(period_start, period_end);

-- Indexes for user_engagement_metrics
CREATE INDEX IF NOT EXISTS idx_user_engagement_user_id ON user_engagement_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_engagement_organization_id ON user_engagement_metrics(organization_id);
CREATE INDEX IF NOT EXISTS idx_user_engagement_date ON user_engagement_metrics(date);

-- Indexes for rag_quality_metrics
CREATE INDEX IF NOT EXISTS idx_rag_quality_user_id ON rag_quality_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_quality_message_id ON rag_quality_metrics(message_id);
CREATE INDEX IF NOT EXISTS idx_rag_quality_created_at ON rag_quality_metrics(created_at);

-- ============================================================================
-- Part 3: Verification
-- ============================================================================
SELECT 'KPI Extraction Tables Created Successfully!' as status;

SELECT
    'agent_performance_metrics: Created' as table_status
UNION ALL
SELECT
    'connector_kpis: Created'
UNION ALL
SELECT
    'user_engagement_metrics: Created'
UNION ALL
SELECT
    'rag_quality_metrics: Created';
