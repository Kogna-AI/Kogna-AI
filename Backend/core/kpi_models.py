"""
KPI Extraction System - Pydantic Models
========================================
This module contains Pydantic models for the KPI extraction and analytics system,
including agent performance tracking, connector KPIs, user engagement metrics,
and RAG quality monitoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class AgentName(str, Enum):
    """Valid AI agent names"""
    TRIAGE = "triage"
    INTERNAL_ANALYST = "internal_analyst"
    RESEARCHER = "researcher"
    SYNTHESIZER = "synthesizer"
    COMMUNICATOR = "communicator"


class ConnectorType(str, Enum):
    """Valid connector types"""
    JIRA = "jira"
    GOOGLE_DRIVE = "google_drive"
    MICROSOFT_EXCEL = "microsoft_excel"
    ASANA = "asana"
    SLACK = "slack"
    GITHUB = "github"
    NOTION = "notion"


class KPICategory(str, Enum):
    """Valid KPI categories"""
    VELOCITY = "velocity"
    BURNDOWN = "burndown"
    COMPLETION_RATE = "completion_rate"
    FINANCIAL = "financial"
    PRODUCTIVITY = "productivity"
    QUALITY = "quality"
    COLLABORATION = "collaboration"


class TrendDirection(str, Enum):
    """Trend direction for KPIs"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    NA = "n/a"


# ============================================================================
# Agent Performance Metrics Models
# ============================================================================

class AgentPerformanceMetricCreate(BaseModel):
    """Model for creating agent performance metrics"""
    user_id: str  # UUID
    organization_id: str  # UUID
    team_id: Optional[str] = None  # UUID
    session_id: Optional[str] = None  # UUID
    message_id: Optional[str] = None  # UUID
    agent_name: AgentName
    response_time_ms: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime
    token_count: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: Decimal = Field(default=0.0, ge=0)
    model_used: Optional[str] = None
    success: bool = True
    error_type: Optional[str] = None
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)


class AgentPerformanceMetricResponse(BaseModel):
    """Model for agent performance metric response"""
    id: int
    user_id: str
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    session_id: Optional[str]
    message_id: Optional[str]
    agent_name: str
    response_time_ms: int
    started_at: datetime
    completed_at: datetime
    token_count: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: Decimal
    model_used: Optional[str]
    success: bool
    error_type: Optional[str]
    confidence_score: Optional[Decimal]
    created_at: datetime
    updated_at: datetime


class AgentPerformanceSummary(BaseModel):
    """Model for aggregated agent performance summary"""
    date: date
    hour: Optional[datetime]
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    agent_name: str
    model_used: Optional[str]
    execution_count: int
    successful_executions: int
    failed_executions: int
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: int
    max_response_time_ms: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    avg_tokens_per_execution: float
    total_cost_usd: Decimal
    avg_cost_per_execution_usd: Decimal
    success_rate_percent: Decimal
    avg_confidence_score: Optional[Decimal]
    min_confidence_score: Optional[Decimal]
    max_confidence_score: Optional[Decimal]
    error_types: List[str]
    period_start: datetime
    period_end: datetime
    last_refreshed: datetime


# ============================================================================
# Connector KPI Models
# ============================================================================

class ConnectorKPICreate(BaseModel):
    """Model for creating connector KPIs"""
    user_id: str  # UUID
    organization_id: str  # UUID
    team_id: Optional[str] = None  # UUID
    sync_job_id: Optional[str] = None  # UUID
    connector_type: ConnectorType
    source_id: str
    source_name: Optional[str] = None
    kpi_category: KPICategory
    kpi_name: str
    kpi_value: Dict[str, Any]  # JSONB
    kpi_unit: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ConnectorKPIResponse(BaseModel):
    """Model for connector KPI response"""
    id: int
    user_id: str
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    sync_job_id: Optional[str]
    connector_type: str
    source_id: str
    source_name: Optional[str]
    kpi_category: str
    kpi_name: str
    kpi_value: Dict[str, Any]
    kpi_unit: Optional[str]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    extracted_at: datetime
    created_at: datetime
    updated_at: datetime


class ConnectorKPITrend(BaseModel):
    """Model for connector KPI trends with analytics"""
    date: date
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    connector_type: str
    kpi_category: str
    kpi_name: str
    kpi_unit: Optional[str]
    source_id: str
    source_name: Optional[str]
    latest_kpi_value: Dict[str, Any]
    sample_count: int
    first_extraction: datetime
    last_extraction: datetime
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    day_over_day_change: Optional[Decimal]
    trend_direction: str
    moving_avg_7day: Optional[Decimal]
    last_refreshed: datetime


# ============================================================================
# User Engagement Metrics Models
# ============================================================================

class UserEngagementMetricCreate(BaseModel):
    """Model for creating user engagement metrics"""
    user_id: str  # UUID
    organization_id: str  # UUID
    team_id: Optional[str] = None  # UUID
    date: date
    session_count: int = Field(default=0, ge=0)
    total_session_duration_seconds: int = Field(default=0, ge=0)
    query_count: int = Field(default=0, ge=0)
    avg_queries_per_session: Decimal = Field(default=0.0, ge=0)
    feedback_count: int = Field(default=0, ge=0)
    avg_satisfaction_score: Optional[Decimal] = Field(None, ge=0, le=5)
    recommendations_viewed: int = Field(default=0, ge=0)
    recommendations_accepted: int = Field(default=0, ge=0)
    common_topics: List[str] = Field(default_factory=list)


class UserEngagementMetricUpdate(BaseModel):
    """Model for updating user engagement metrics"""
    session_count: Optional[int] = Field(None, ge=0)
    total_session_duration_seconds: Optional[int] = Field(None, ge=0)
    query_count: Optional[int] = Field(None, ge=0)
    avg_queries_per_session: Optional[Decimal] = Field(None, ge=0)
    feedback_count: Optional[int] = Field(None, ge=0)
    avg_satisfaction_score: Optional[Decimal] = Field(None, ge=0, le=5)
    recommendations_viewed: Optional[int] = Field(None, ge=0)
    recommendations_accepted: Optional[int] = Field(None, ge=0)
    common_topics: Optional[List[str]] = None


class UserEngagementMetricResponse(BaseModel):
    """Model for user engagement metric response"""
    id: int
    user_id: str
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    date: date
    session_count: int
    total_session_duration_seconds: int
    query_count: int
    avg_queries_per_session: Decimal
    feedback_count: int
    avg_satisfaction_score: Optional[Decimal]
    recommendations_viewed: int
    recommendations_accepted: int
    common_topics: List[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# RAG Quality Metrics Models
# ============================================================================

class RAGQualityMetricCreate(BaseModel):
    """Model for creating RAG quality metrics"""
    user_id: str  # UUID
    organization_id: Optional[str] = None  # UUID
    team_id: Optional[str] = None  # UUID
    message_id: Optional[str] = None  # UUID
    retrieval_count: int = Field(default=0, ge=0)
    avg_similarity_score: Optional[Decimal] = Field(None, ge=0, le=1)
    sources_used: List[Dict[str, Any]] = Field(default_factory=list)
    user_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    citation_accuracy: Optional[Decimal] = Field(None, ge=0, le=1)
    answer_relevance: Optional[Decimal] = Field(None, ge=0, le=1)


class RAGQualityMetricResponse(BaseModel):
    """Model for RAG quality metric response"""
    id: int
    user_id: str
    organization_id: Optional[str]  # UUID
    team_id: Optional[str]  # UUID
    message_id: Optional[str]
    retrieval_count: int
    avg_similarity_score: Optional[Decimal]
    sources_used: List[Dict[str, Any]]
    user_satisfaction: Optional[int]
    citation_accuracy: Optional[Decimal]
    answer_relevance: Optional[Decimal]
    created_at: datetime


# ============================================================================
# Extended Models for Existing Tables
# ============================================================================

class AgentTraceExtended(BaseModel):
    """Extended model for agent traces with performance metrics"""
    id: int
    user_id: str
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    session_id: Optional[str]
    message_id: Optional[str]
    agent_name: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    execution_time_ms: Optional[int]
    token_count: Optional[int]
    model_used: Optional[str]
    created_at: datetime


class SyncJobExtended(BaseModel):
    """Extended model for sync jobs with KPI extraction metrics"""
    id: str  # UUID
    user_id: str  # UUID
    organization_id: str  # UUID
    team_id: Optional[str]  # UUID
    connector_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    items_processed: int
    items_failed: int
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    kpis_extracted: int
    kpi_extraction_time_ms: Optional[int]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Utility Models
# ============================================================================

class KPIMetricsSummary(BaseModel):
    """Summary model for KPI metrics across all tables"""
    total_agent_executions: int
    total_kpis_extracted: int
    total_active_users: int
    avg_user_satisfaction: Optional[Decimal]
    total_cost_usd: Decimal
    period_start: datetime
    period_end: datetime


class PerformanceStats(BaseModel):
    """Performance statistics model"""
    metric_name: str
    current_value: float
    previous_value: Optional[float]
    change_percent: Optional[float]
    trend: TrendDirection
    unit: Optional[str]


# ============================================================================
# Dashboard & API Response Models
# ============================================================================

class AgentPerformanceKPI(BaseModel):
    """Agent performance KPIs for dashboard"""
    avg_response_time_ms: float
    total_queries: int
    total_cost_usd: Decimal
    success_rate: float
    by_agent: List[Dict[str, Any]] = Field(default_factory=list)


class ConnectorKPI(BaseModel):
    """Connector KPIs for dashboard"""
    connector_type: str
    total_syncs: int
    total_kpis_extracted: int
    last_sync: Optional[datetime]
    kpis_by_category: Dict[str, int] = Field(default_factory=dict)


class UserEngagementKPI(BaseModel):
    """User engagement KPIs for dashboard"""
    active_users: int
    avg_satisfaction: Optional[Decimal]
    total_sessions: int
    total_queries: int
    avg_session_duration_seconds: float


class KPIDashboard(BaseModel):
    """Comprehensive KPI dashboard response"""
    agent_performance: AgentPerformanceKPI
    connector_kpis: Dict[str, ConnectorKPI]
    user_engagement: UserEngagementKPI
    period_start: datetime
    period_end: datetime


class KPITrendPoint(BaseModel):
    """Single point in a KPI trend time-series"""
    timestamp: datetime
    value: Any
    metadata: Optional[Dict[str, Any]] = None


class FeedbackSubmission(BaseModel):
    """User feedback submission for satisfaction tracking"""
    message_id: str
    satisfaction_score: int = Field(ge=1, le=5)
    feedback_text: Optional[str] = None


class KPIExportParams(BaseModel):
    """Parameters for KPI export requests"""
    format: str = Field(default="json", pattern="^(json|csv)$")
    kpi_types: Optional[List[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
