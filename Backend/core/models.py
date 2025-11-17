from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, date

# ====== Success Response ======
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

# ====== Organizations ======
class OrganizationCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    team_due: Optional[int] = None
    team: Optional[str] = None
    project_number: Optional[int] = 0

# ====== Users ======
class UserCreate(BaseModel):
    supabase_id: str
    organization_id: int
    first_name: str
    second_name: Optional[str] = None
    role: Optional[str] = None
    email: EmailStr

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    second_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    supabase_id: str
    organization_id: int
    first_name: str
    second_name: Optional[str]
    role: Optional[str]
    email: str
    created_at: datetime

# ====== Teams ======
class TeamCreate(BaseModel):
    organization_id: int
    name: str

class TeamMemberAdd(BaseModel):
    team_id: int
    user_id: int
    role: Optional[str] = None
    performance: Optional[float] = None
    capacity: Optional[float] = None

# ====== Objectives ======
class ObjectiveCreate(BaseModel):
    organization_id: int
    title: str
    progress: float = Field(default=0, ge=0, le=100)
    status: str = "on-track"
    team_responsible: Optional[str] = None

class ObjectiveUpdate(BaseModel):
    title: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    team_responsible: Optional[str] = None

class GrowthStageCreate(BaseModel):
    objective_id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class MilestoneCreate(BaseModel):
    growth_stage_id: int
    title: str
    achieved: bool = False

# ====== Metrics ======
class MetricCreate(BaseModel):
    organization_id: int
    name: str
    value: float
    unit: Optional[str] = None
    change_from_last: Optional[float] = None

# ====== AI Insights ======
class AIInsightCreate(BaseModel):
    organization_id: int
    category: str
    title: str
    description: str
    confidence: float = Field(ge=0, le=100)
    level: str

# ====== Recommendations ======
class RecommendationCreate(BaseModel):
    organization_id: int
    title: str
    recommendation: str
    confidence: float = Field(ge=0, le=100)
    action: Optional[str] = None
    created_for: Optional[int] = None

class RecommendationReasonCreate(BaseModel):
    recommendation_id: int
    reason: str
    evidence_datasets_id: Optional[Dict] = None

# ====== Actions ======
class ActionCreate(BaseModel):
    user_id: int
    recommendation_id: Optional[int] = None
    action_taken: str
    result: Optional[str] = None


#Authentication
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

# Authentication
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    second_name: Optional[str] = None
    role: Optional[str] = None
    organization_id: int

class AuthResponse(BaseModel):
    success: bool = True
    token: str
    user: Dict[str, Any]