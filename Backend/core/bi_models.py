"""
BI Embedding Framework - Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class BIProvider(str, Enum):
    TABLEAU = "tableau"
    POWERBI = "powerbi"
    LOOKER = "looker"
    SUPERSET = "superset"
    METABASE = "metabase"


class BIConnectorStatus(str, Enum):
    CONFIGURED = "configured"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"


# ============================================================================
# Request Models
# ============================================================================

class BIConnectorCreate(BaseModel):
    provider: BIProvider
    display_name: Optional[str] = None
    server_url: str
    site_name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    embed_secret: Optional[str] = None
    tenant_id: Optional[str] = None        # Power BI
    workspace_id: Optional[str] = None     # Power BI
    config: Dict[str, Any] = {}


class BIConnectorUpdate(BaseModel):
    display_name: Optional[str] = None
    server_url: Optional[str] = None
    site_name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    embed_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    workspace_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class BIDashboardRegister(BaseModel):
    bi_connector_id: str
    external_dashboard_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    embed_url: Optional[str] = None
    embed_config: Dict[str, Any] = {}
    is_default: bool = False
    is_public: bool = True


class FeedbackSubmission(BaseModel):
    """Re-export for consistency (also in kpi_models)"""
    message_id: str
    satisfaction_score: int = Field(ge=1, le=5)
    feedback_text: Optional[str] = None


# ============================================================================
# Response Models
# ============================================================================

class BIConnectorResponse(BaseModel):
    id: str
    provider: str
    display_name: Optional[str]
    server_url: str
    site_name: Optional[str]
    status: str
    last_verified_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    dashboard_count: int = 0


class BIDashboardResponse(BaseModel):
    id: str
    bi_connector_id: str
    external_dashboard_id: Optional[str]
    name: str
    description: Optional[str]
    embed_url: Optional[str]
    is_default: bool
    provider: Optional[str] = None
    created_at: datetime


class EmbedTokenResponse(BaseModel):
    embed_url: str
    token: Optional[str] = None
    token_type: str = "bearer"
    expires_at: Optional[int] = None
    provider: str
    dashboard_id: str


# ============================================================================
# Executive Dashboard Models (Native KPI View)
# ============================================================================

class ExecKPISummaryCard(BaseModel):
    category: str               # incidents, problems, requests
    total_ytd: int
    active: int
    overdue_percent: float
    trend_direction: str        # up, down, stable
    change_percent: float
    monthly_trend: List[Dict[str, Any]]   # [{month, value}]
    breakdown: Dict[str, Any]             # {category: {count, yoy_change}}
    sla_compliance: Optional[float] = None
    avg_resolution_time: Optional[str] = None


class ExecDashboardResponse(BaseModel):
    incidents: ExecKPISummaryCard
    problems: ExecKPISummaryCard
    requests: ExecKPISummaryCard
    last_updated: datetime
    period_label: str   # "2026 YTD"
