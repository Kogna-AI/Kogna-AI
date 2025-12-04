from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import os
from dotenv import load_dotenv
from contextlib import contextmanager
import json
import asyncio
import jwt
import bcrypt



load_dotenv()
# Load Ai_agents/.env for API keys but don't override existing vars
load_dotenv(dotenv_path="Ai_agents/.env", override=False)

# Security Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-this")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))
security = HTTPBearer()


# FastAPI config

app = FastAPI(
    title="Kogna-AI API",
    description="AI-Powered Strategic Management Dashboard",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# include ROUTERS
from routers.Authentication import router as auth_router
from routers.users import router as users_router
from routers.connectors import connect_router, callback_router
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(connect_router)
app.include_router(callback_router)


# Database Connection
@contextmanager
def get_db():
    """Database connection context manager"""
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()


# Authentication Helper Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user_id


# Pydantic Models

# Base Response
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

# Organizations
class OrganizationCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    team_due: Optional[int] = None
    team: Optional[str] = None
    project_number: Optional[int] = 0

class OrganizationResponse(BaseModel):
    id: int
    name: str
    industry: Optional[str]
    project_number: int
    created_at: datetime

# Users
class UserCreate(BaseModel):
    organization_id: int
    first_name: str
    second_name: Optional[str] = None
    role: Optional[str] = None
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    organization_id: int
    first_name: str
    second_name: Optional[str]
    role: Optional[str]
    email: str
    created_at: datetime

# Teams
class TeamCreate(BaseModel):
    organization_id: int
    name: str

class TeamMemberAdd(BaseModel):
    team_id: int
    user_id: int
    role: Optional[str] = None
    performance: Optional[float] = None
    capacity: Optional[float] = None

# Objectives
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

# Metrics
class MetricCreate(BaseModel):
    organization_id: int
    name: str
    value: float
    unit: Optional[str] = None
    change_from_last: Optional[float] = None

# AI Insights
class AIInsightCreate(BaseModel):
    organization_id: int
    category: str  # 'opportunity', 'risk', 'insight'
    title: str
    description: str
    confidence: float = Field(ge=0, le=100)
    level: str  # 'low', 'medium', 'high'

# Recommendations
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

# Meetings
class MeetingCreate(BaseModel):
    organization_id: int
    title: str
    category: str  # 'strategy', 'product', 'team', 'all-strategy'
    scheduled_time: datetime
    duration: Optional[int] = None

class MeetingAttendeeAdd(BaseModel):
    meeting_id: int
    user_id: int

# Actions
class ActionCreate(BaseModel):
    user_id: int
    recommendation_id: Optional[int] = None
    action_taken: str
    result: Optional[str] = None  # 'success', 'intermediate', 'fail'

# Data Sources
class DataSourceCreate(BaseModel):
    organization_id: int
    name: str
    connection_info: Dict

class DatasetCreate(BaseModel):
    data_source_id: int
    name: str
    schema: Optional[Dict] = None
    data_refresh_rate: Optional[str] = None

class DataRecordCreate(BaseModel):
    dataset_id: int
    record_data: Dict

# Feedback
class FeedbackCreate(BaseModel):
    user_id: int
    rating: int = Field(ge=1, le=5)
    comments: Optional[str] = None

# AI Agent Requests
class AIAnalysisRequest(BaseModel):
    organization_id: int
    analysis_type: str  # 'qbr', 'risks', 'kpis', 'revenue', 'churn', 'projects'
    parameters: Optional[Dict] = None


#Health Check
@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "KognaDash API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/health")
def health_check():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.execute("SELECT COUNT(*) FROM organizations")
            org_count = cursor.fetchone()['count']
            return {
                "status": "healthy",
                "database": "connected",
                "organizations": org_count
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

# @app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
# def register(data: RegisterRequest):
#     """Register a new user"""
#     with get_db() as conn:
#         cursor = conn.cursor()

#         # Check if user already exists
#         cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
#         if cursor.fetchone():
#             raise HTTPException(status_code=400, detail="Email already registered")

#         # Check if password column exists, if not add it
#         cursor.execute("""
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_name='users' AND column_name='password_hash'
#         """)
#         if not cursor.fetchone():
#             cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
#             conn.commit()

#         # Hash password and create user
#         hashed_password = hash_password(data.password)
#         cursor.execute("""
#             INSERT INTO users (organization_id, first_name, second_name, role, email, password_hash)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             RETURNING id, organization_id, first_name, second_name, role, email, created_at
#         """, (data.organization_id, data.first_name, data.second_name, data.role, data.email, hashed_password))

#         user = cursor.fetchone()
#         conn.commit()

#         # Create JWT token
#         token = create_access_token({"user_id": user['id'], "email": user['email']})

#         return {
#             "success": True,
#             "token": token,
#             "user": dict(user)
#         }


# @app.post("/api/auth/login")
# def login(data: LoginRequest):
#     """Login user and return JWT token"""
#     with get_db() as conn:
#         cursor = conn.cursor()

#         # Check if password column exists
#         cursor.execute("""
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_name='users' AND column_name='password_hash'
#         """)
#         password_column_exists = cursor.fetchone()

#         if not password_column_exists:
#             # For demo purposes, allow login without password
#             cursor.execute("""
#                 SELECT id, organization_id, first_name, second_name, role, email, created_at
#                 FROM users WHERE email = %s
#             """, (data.email,))
#             user = cursor.fetchone()

#             if not user:
#                 raise HTTPException(status_code=401, detail="Invalid email or password")

#             # Create JWT token
#             token = create_access_token({"user_id": user['id'], "email": user['email']})

#             return {
#                 "success": True,
#                 "token": token,
#                 "user": dict(user)
#             }

#         # Get user with password hash
#         cursor.execute("""
#             SELECT id, organization_id, first_name, second_name, role, email, password_hash, created_at
#             FROM users WHERE email = %s
#         """, (data.email,))

#         user = cursor.fetchone()

#         if not user:
#             raise HTTPException(status_code=401, detail="Invalid email or password")

#         # Check if user has no password set 
#         if user['password_hash'] is None:
#             # Allow login without password verification for users with null password_hash
#             user_data = {k: v for k, v in user.items() if k != 'password_hash'}
#             token = create_access_token({"user_id": user['id'], "email": user['email']})
#             return {
#                 "success": True,
#                 "token": token,
#                 "user": user_data
#             }

#         # Verify password
#         if not verify_password(data.password, user['password_hash']):
#             raise HTTPException(status_code=401, detail="Invalid email or password")

#         # Remove password_hash from user dict
#         user_data = {k: v for k, v in user.items() if k != 'password_hash'}

#         # Create JWT token
#         token = create_access_token({"user_id": user['id'], "email": user['email']})

#         return {
#             "success": True,
#             "token": token,
#             "user": user_data
#         }


# @app.get("/api/auth/me")
# async def get_current_user_info(user_id: int = Depends(get_current_user)):
#     """Get current authenticated user information"""
#     with get_db() as conn:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT id, organization_id, first_name, second_name, role, email, created_at
#             FROM users WHERE id = %s
#         """, (user_id,))
#         user = cursor.fetchone()

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         return {"success": True, "data": user}

# ============================================================================
# ORGANIZATIONS ENDPOINTS
# ============================================================================

@app.post("/api/organizations", status_code=status.HTTP_201_CREATED)
def create_organization(org: OrganizationCreate):
    """Create a new organization"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO organizations (name, industry, team_due, team, project_number)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (org.name, org.industry, org.team_due, org.team, org.project_number))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/organizations/{org_id}")
def get_organization(org_id: int):
    """Get organization by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations WHERE id = %s", (org_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Organization not found")
        return {"success": True, "data": result}

@app.get("/api/organizations")
def list_organizations():
    """List all organizations"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations ORDER BY created_at DESC")
        return {"success": True, "data": cursor.fetchall()}

@app.put("/api/organizations/{org_id}")
def update_organization(org_id: int, org: OrganizationCreate):
    """Update organization"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE organizations 
            SET name = %s, industry = %s, team_due = %s, team = %s, project_number = %s
            WHERE id = %s
            RETURNING *
        """, (org.name, org.industry, org.team_due, org.team, org.project_number, org_id))
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="Organization not found")
        return {"success": True, "data": result}

@app.delete("/api/organizations/{org_id}")
def delete_organization(org_id: int):
    """Delete organization"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM organizations WHERE id = %s RETURNING id", (org_id,))
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="Organization not found")
        return {"success": True, "message": "Organization deleted"}

@app.get("/api/organizations/{org_id}/dashboard")
def get_organization_dashboard(org_id: int):
    """Get comprehensive dashboard data"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Use the view we created
        cursor.execute("SELECT * FROM organization_dashboard WHERE id = %s", (org_id,))
        dashboard = cursor.fetchone()
        
        if not dashboard:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get recent metrics
        cursor.execute("""
            SELECT name, value, unit, change_from_last, last_updated
            FROM metrics
            WHERE organization_id = %s
            ORDER BY last_updated DESC
            LIMIT 10
        """, (org_id,))
        recent_metrics = cursor.fetchall()
        
        # Get at-risk objectives
        cursor.execute("""
            SELECT id, title, progress, status, team_responsible
            FROM objectives
            WHERE organization_id = %s AND status = 'at-risk'
            ORDER BY progress ASC
            LIMIT 5
        """, (org_id,))
        at_risk_objectives = cursor.fetchall()
        
        # Get active insights
        cursor.execute("""
            SELECT id, category, title, confidence, level, created_at
            FROM ai_insights
            WHERE organization_id = %s AND status = 'active'
            ORDER BY confidence DESC, created_at DESC
            LIMIT 5
        """, (org_id,))
        active_insights = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "overview": dashboard,
                "recent_metrics": recent_metrics,
                "at_risk_objectives": at_risk_objectives,
                "active_insights": active_insights
            }
        }

# ============================================================================
# USERS ENDPOINTS
# ============================================================================

@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    """Create a new user"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (organization_id, first_name, second_name, role, email)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            """, (user.organization_id, user.first_name, user.second_name, user.role, user.email))
            result = cursor.fetchone()
            conn.commit()
            return {"success": True, "data": result}
        except psycopg2.IntegrityError as e:
            raise HTTPException(status_code=400, detail="Email already exists")

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": result}

@app.get("/api/organizations/{org_id}/users")
def list_organization_users(org_id: int):
    """List all users in organization"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.*, 
                   COUNT(tm.id) as team_count,
                   AVG(tm.performance) as avg_performance
            FROM users u
            LEFT JOIN team_members tm ON tm.user_id = u.id
            WHERE u.organization_id = %s
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}

@app.put("/api/users/{user_id}")
def update_user(user_id: int, user: UserCreate):
    """Update user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET first_name = %s, second_name = %s, role = %s, email = %s
            WHERE id = %s
            RETURNING *
        """, (user.first_name, user.second_name, user.role, user.email, user_id))
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": result}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    """Delete user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "message": "User deleted"}

# ============================================================================
# TEAMS ENDPOINTS
# ============================================================================

@app.post("/api/teams", status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate):
    """Create a new team"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teams (organization_id, name)
            VALUES (%s, %s)
            RETURNING *
        """, (team.organization_id, team.name))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/teams/{team_id}")
def get_team(team_id: int):
    """Get team with members"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM teams WHERE id = %s", (team_id,))
        team = cursor.fetchone()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        cursor.execute("""
            SELECT tm.*, u.first_name, u.second_name, u.email, u.role as user_role
            FROM team_members tm
            JOIN users u ON u.id = tm.user_id
            WHERE tm.team_id = %s
        """, (team_id,))
        members = cursor.fetchall()
        
        cursor.execute("""
            SELECT skill_name, COUNT(*) as member_count, AVG(
                CASE proficiency
                    WHEN 'expert' THEN 5
                    WHEN 'advanced' THEN 4
                    WHEN 'intermediate' THEN 3
                    WHEN 'beginner' THEN 2
                    ELSE 1
                END
            ) as avg_proficiency
            FROM team_skills
            WHERE team_id = %s
            GROUP BY skill_name
        """, (team_id,))
        skills = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                **team,
                "members": members,
                "skills": skills
            }
        }

@app.post("/api/teams/members")
def add_team_member(member: TeamMemberAdd):
    """Add member to team"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO team_members (team_id, user_id, role, performance, capacity, status)
                VALUES (%s, %s, %s, %s, %s, 'available')
                RETURNING *
            """, (member.team_id, member.user_id, member.role, member.performance, member.capacity))
            result = cursor.fetchone()
            conn.commit()
            return {"success": True, "data": result}
        except psycopg2.IntegrityError:
            raise HTTPException(status_code=400, detail="User already in team")

@app.get("/api/organizations/{org_id}/teams")
def list_organization_teams(org_id: int):
    """List teams with performance summary"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM team_performance_summary
            WHERE organization_id = %s
            ORDER BY avg_performance DESC NULLS LAST
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}

# ============================================================================
# OBJECTIVES ENDPOINTS
# ============================================================================

@app.post("/api/objectives", status_code=status.HTTP_201_CREATED)
def create_objective(obj: ObjectiveCreate):
    """Create objective"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO objectives (organization_id, title, progress, status, team_responsible)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (obj.organization_id, obj.title, obj.progress, obj.status, obj.team_responsible))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/objectives/{obj_id}")
def get_objective(obj_id: int):
    """Get objective with growth stages and milestones"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM objectives WHERE id = %s", (obj_id,))
        objective = cursor.fetchone()
        if not objective:
            raise HTTPException(status_code=404, detail="Objective not found")
        
        cursor.execute("""
            SELECT gs.*,
                   json_agg(
                       json_build_object(
                           'id', m.id,
                           'title', m.title,
                           'achieved', m.boolean,
                           'achieved_at', m.achieved_at
                       ) ORDER BY m.created_at
                   ) FILTER (WHERE m.id IS NOT NULL) as milestones
            FROM growth_stages gs
            LEFT JOIN milestones m ON m.growth_stage_id = gs.id
            WHERE gs.objective_id = %s
            GROUP BY gs.id
            ORDER BY gs.start_date
        """, (obj_id,))
        stages = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                **objective,
                "growth_stages": stages
            }
        }

@app.put("/api/objectives/{obj_id}")
def update_objective(obj_id: int, obj: ObjectiveUpdate):
    """Update objective"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if obj.title is not None:
            updates.append("title = %s")
            params.append(obj.title)
        if obj.progress is not None:
            updates.append("progress = %s")
            params.append(obj.progress)
            # Auto-update status based on progress
            if obj.progress >= 80:
                updates.append("status = 'ahead'")
            elif obj.progress >= 50:
                updates.append("status = 'on-track'")
            else:
                updates.append("status = 'at-risk'")
        if obj.status is not None:
            updates.append("status = %s")
            params.append(obj.status)
        if obj.team_responsible is not None:
            updates.append("team_responsible = %s")
            params.append(obj.team_responsible)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(obj_id)
        query = f"UPDATE objectives SET {', '.join(updates)} WHERE id = %s RETURNING *"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail="Objective not found")
        return {"success": True, "data": result}

@app.get("/api/organizations/{org_id}/objectives")
def list_objectives(org_id: int, status: Optional[str] = None):
    """List objectives"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT o.*, 
                       COUNT(gs.id) as stage_count,
                       COUNT(m.id) as milestone_count,
                       COUNT(CASE WHEN m.boolean = true THEN 1 END) as completed_milestones
                FROM objectives o
                LEFT JOIN growth_stages gs ON gs.objective_id = o.id
                LEFT JOIN milestones m ON m.growth_stage_id = gs.id
                WHERE o.organization_id = %s AND o.status = %s
                GROUP BY o.id
                ORDER BY o.progress ASC
            """, (org_id, status))
        else:
            cursor.execute("""
                SELECT o.*, 
                       COUNT(gs.id) as stage_count,
                       COUNT(m.id) as milestone_count,
                       COUNT(CASE WHEN m.boolean = true THEN 1 END) as completed_milestones
                FROM objectives o
                LEFT JOIN growth_stages gs ON gs.objective_id = o.id
                LEFT JOIN milestones m ON m.growth_stage_id = gs.id
                WHERE o.organization_id = %s
                GROUP BY o.id
                ORDER BY o.created_at DESC
            """, (org_id,))
        
        return {"success": True, "data": cursor.fetchall()}

@app.post("/api/growth-stages", status_code=status.HTTP_201_CREATED)
def create_growth_stage(stage: GrowthStageCreate):
    """Create growth stage"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO growth_stages (objective_id, name, description, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (stage.objective_id, stage.name, stage.description, stage.start_date, stage.end_date))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.post("/api/milestones", status_code=status.HTTP_201_CREATED)
def create_milestone(milestone: MilestoneCreate):
    """Create milestone"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO milestones (growth_stage_id, title, boolean, achieved_at)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """, (milestone.growth_stage_id, milestone.title, milestone.achieved, 
              datetime.now() if milestone.achieved else None))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.put("/api/milestones/{milestone_id}/achieve")
def achieve_milestone(milestone_id: int):
    """Mark milestone as achieved"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE milestones 
            SET boolean = true, achieved_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
        """, (milestone_id,))
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="Milestone not found")
        return {"success": True, "data": result}

# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@app.post("/api/metrics", status_code=status.HTTP_201_CREATED)
def create_metric(metric: MetricCreate):
    """Create/log metric"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics (organization_id, name, value, unit, change_from_last)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (metric.organization_id, metric.name, metric.value, metric.unit, metric.change_from_last))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/metrics/{metric_id}")
def get_metric(metric_id: int):
    """Get metric by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metrics WHERE id = %s", (metric_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Metric not found")
        return {"success": True, "data": result}

@app.get("/api/organizations/{org_id}/metrics")
def list_metrics(org_id: int, name: Optional[str] = None, limit: int = 100):
    """List metrics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if name:
            cursor.execute("""
                SELECT * FROM metrics 
                WHERE organization_id = %s AND name ILIKE %s
                ORDER BY last_updated DESC
                LIMIT %s
            """, (org_id, f"%{name}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM metrics 
                WHERE organization_id = %s
                ORDER BY last_updated DESC
                LIMIT %s
            """, (org_id, limit))
        
        return {"success": True, "data": cursor.fetchall()}

@app.get("/api/organizations/{org_id}/metrics/trends")
def get_metric_trends(org_id: int):
    """Get metric trends over time"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                name,
                json_agg(
                    json_build_object(
                        'value', value,
                        'unit', unit,
                        'change', change_from_last,
                        'timestamp', last_updated
                    ) ORDER BY last_updated
                ) as history
            FROM metrics
            WHERE organization_id = %s
            GROUP BY name
            ORDER BY name
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}

# ============================================================================
# AI INSIGHTS ENDPOINTS
# ============================================================================

@app.post("/api/insights", status_code=status.HTTP_201_CREATED)
def create_insight(insight: AIInsightCreate):
    """Create AI insight"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_insights (organization_id, category, title, description, confidence, level)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (insight.organization_id, insight.category, insight.title, 
              insight.description, insight.confidence, insight.level))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/insights/{insight_id}")
def get_insight(insight_id: int):
    """Get insight by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_insights WHERE id = %s", (insight_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Insight not found")
        return {"success": True, "data": result}

@app.get("/api/organizations/{org_id}/insights")
def list_insights(
    org_id: int, 
    category: Optional[str] = None,
    level: Optional[str] = None,
    status: str = "active"
):
    """List AI insights"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM ai_insights WHERE organization_id = %s"
        params = [org_id]
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        if level:
            query += " AND level = %s"
            params.append(level)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY level DESC, confidence DESC, created_at DESC LIMIT 50"
        
        cursor.execute(query, params)
        return {"success": True, "data": cursor.fetchall()}

@app.put("/api/insights/{insight_id}/archive")
def archive_insight(insight_id: int):
    """Archive insight"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ai_insights SET status = 'archived'
            WHERE id = %s
            RETURNING *
        """, (insight_id,))
        result = cursor.fetchone()
        conn.commit()
        if not result:
            raise HTTPException(status_code=404, detail="Insight not found")
        return {"success": True, "data": result}

# ============================================================================
# RECOMMENDATIONS ENDPOINTS
# ============================================================================

@app.post("/api/recommendations", status_code=status.HTTP_201_CREATED)
def create_recommendation(rec: RecommendationCreate):
    """Create a new recommendation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recommendations (organization_id, title, recommendation, confidence, action, created_for)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (rec.organization_id, rec.title, rec.recommendation, 
              rec.confidence, rec.action, rec.created_for))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/recommendations/{rec_id}")
def get_recommendation(rec_id: int):
    """Get recommendation by ID with reasons"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get recommendation
        cursor.execute("""
            SELECT r.*, 
                   u.first_name || ' ' || COALESCE(u.second_name, '') as created_for_name
            FROM recommendations r
            LEFT JOIN users u ON u.id = r.created_for
            WHERE r.id = %s
        """, (rec_id,))
        recommendation = cursor.fetchone()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        # Get reasons/evidence
        cursor.execute("""
            SELECT rr.*, 
                   ds.name as dataset_name
            FROM recommendation_reasons rr
            LEFT JOIN datasets ds ON ds.id = (rr.evidence_datasets_id->>'id')::int
            WHERE rr.recommendation_id = %s
            ORDER BY rr.created_at
        """, (rec_id,))
        reasons = cursor.fetchall()
        
        # Get actions taken
        cursor.execute("""
            SELECT a.*, u.first_name || ' ' || COALESCE(u.second_name, '') as user_name
            FROM actions a
            JOIN users u ON u.id = a.user_id
            WHERE a.recommendation_id = %s
            ORDER BY a.taken_at DESC
        """, (rec_id,))
        actions = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                **recommendation,
                "reasons": reasons,
                "actions": actions
            }
        }

@app.get("/api/organizations/{org_id}/recommendations")
def list_recommendations(
    org_id: int, 
    status: Optional[str] = None,
    created_for: Optional[int] = None,
    min_confidence: Optional[float] = None
):
    """List recommendations for organization with filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT r.*, 
                   u.first_name || ' ' || COALESCE(u.second_name, '') as created_for_name,
                   COUNT(DISTINCT rr.id) as reason_count,
                   COUNT(DISTINCT a.id) as action_count
            FROM recommendations r
            LEFT JOIN users u ON u.id = r.created_for
            LEFT JOIN recommendation_reasons rr ON rr.recommendation_id = r.id
            LEFT JOIN actions a ON a.recommendation_id = r.id
            WHERE r.organization_id = %s
        """
        params = [org_id]
        
        if status:
            query += " AND r.status = %s"
            params.append(status)
        
        if created_for:
            query += " AND r.created_for = %s"
            params.append(created_for)
        
        if min_confidence:
            query += " AND r.confidence >= %s"
            params.append(min_confidence)
        
        query += """
            GROUP BY r.id, u.first_name, u.second_name
            ORDER BY r.confidence DESC, r.created_at DESC
            LIMIT 100
        """
        
        cursor.execute(query, params)
        return {"success": True, "data": cursor.fetchall()}

@app.get("/api/organizations/{org_id}/recommendations/pending")
def list_pending_recommendations(org_id: int):
    """Get all pending recommendations that need action"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, 
                   u.first_name || ' ' || COALESCE(u.second_name, '') as created_for_name,
                   COUNT(DISTINCT rr.id) as evidence_count,
                   EXTRACT(DAY FROM CURRENT_TIMESTAMP - r.created_at) as days_pending
            FROM recommendations r
            LEFT JOIN users u ON u.id = r.created_for
            LEFT JOIN recommendation_reasons rr ON rr.recommendation_id = r.id
            WHERE r.organization_id = %s AND r.status = 'pending'
            GROUP BY r.id, u.first_name, u.second_name
            ORDER BY r.confidence DESC, days_pending DESC
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}

@app.get("/api/organizations/{org_id}/recommendations/high-priority")
def get_high_priority_recommendations(org_id: int):
    """Get high confidence, pending recommendations that need immediate attention"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, 
                   u.first_name || ' ' || COALESCE(u.second_name, '') as assigned_to,
                   COUNT(DISTINCT rr.id) as evidence_count
            FROM recommendations r
            LEFT JOIN users u ON u.id = r.created_for
            LEFT JOIN recommendation_reasons rr ON rr.recommendation_id = r.id
            WHERE r.organization_id = %s 
              AND r.status = 'pending'
              AND r.confidence >= 70
            GROUP BY r.id, u.first_name, u.second_name
            ORDER BY r.confidence DESC
            LIMIT 10
        """, (org_id,))
        return {"success": True, "data": cursor.fetchall()}

@app.put("/api/recommendations/{rec_id}/status")
def update_recommendation_status(rec_id: int, new_status: str):
    """Update recommendation status (pending/acted/dismissed)"""
    if new_status not in ['pending', 'acted', 'dismissed']:
        raise HTTPException(
            status_code=400, 
            detail="Status must be one of: pending, acted, dismissed"
        )
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE recommendations 
            SET status = %s
            WHERE id = %s
            RETURNING *
        """, (new_status, rec_id))
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {"success": True, "data": result}

@app.put("/api/recommendations/{rec_id}")
def update_recommendation(rec_id: int, rec: RecommendationCreate):
    """Update recommendation details"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE recommendations 
            SET title = %s, 
                recommendation = %s, 
                confidence = %s, 
                action = %s,
                created_for = %s
            WHERE id = %s
            RETURNING *
        """, (rec.title, rec.recommendation, rec.confidence, rec.action, 
              rec.created_for, rec_id))
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {"success": True, "data": result}

@app.delete("/api/recommendations/{rec_id}")
def delete_recommendation(rec_id: int):
    """Delete recommendation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM recommendations 
            WHERE id = %s 
            RETURNING id
        """, (rec_id,))
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {"success": True, "message": "Recommendation deleted"}

@app.post("/api/recommendations/{rec_id}/reasons", status_code=status.HTTP_201_CREATED)
def add_recommendation_reason(rec_id: int, reason: RecommendationReasonCreate):
    """Add supporting reason/evidence to recommendation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recommendation_reasons (recommendation_id, reason, evidence_datasets_id)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (rec_id, reason.reason, Json(reason.evidence_datasets_id) if reason.evidence_datasets_id else None))
        result = cursor.fetchone()
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/recommendations/{rec_id}/reasons")
def get_recommendation_reasons(rec_id: int):
    """Get all reasons/evidence for a recommendation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rr.*, 
                   ds.name as dataset_name,
                   src.name as data_source_name
            FROM recommendation_reasons rr
            LEFT JOIN datasets ds ON ds.id = (rr.evidence_datasets_id->>'dataset_id')::int
            LEFT JOIN data_sources src ON src.id = ds.data_source_id
            WHERE rr.recommendation_id = %s
            ORDER BY rr.created_at
        """, (rec_id,))
        return {"success": True, "data": cursor.fetchall()}

@app.get("/api/organizations/{org_id}/recommendations/stats")
def get_recommendation_stats(org_id: int):
    """Get recommendation statistics and effectiveness"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_recommendations,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'acted') as acted,
                COUNT(*) FILTER (WHERE status = 'dismissed') as dismissed,
                AVG(confidence) as avg_confidence,
                COUNT(*) FILTER (WHERE confidence >= 80) as high_confidence_count
            FROM recommendations
            WHERE organization_id = %s
        """, (org_id,))
        overall_stats = cursor.fetchone()
        
        # Action rate by confidence level
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN confidence >= 80 THEN 'High (80-100)'
                    WHEN confidence >= 60 THEN 'Medium (60-79)'
                    ELSE 'Low (0-59)'
                END as confidence_range,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'acted') as acted,
                ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'acted') / COUNT(*), 2) as action_rate
            FROM recommendations
            WHERE organization_id = %s
            GROUP BY confidence_range
            ORDER BY confidence_range
        """, (org_id,))
        action_by_confidence = cursor.fetchall()
        
        # Recent trend (last 30 days)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as created,
                COUNT(*) FILTER (WHERE status = 'acted') as acted
            FROM recommendations
            WHERE organization_id = %s
              AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (org_id,))
        recent_trend = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "overall": overall_stats,
                "action_by_confidence": action_by_confidence,
                "recent_trend": recent_trend
            }
        }

@app.post("/api/recommendations/{rec_id}/assign")
def assign_recommendation(rec_id: int, user_id: int):
    """Assign recommendation to a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update recommendation
        cursor.execute("""
            UPDATE recommendations 
            SET created_for = %s
            WHERE id = %s
            RETURNING *
        """, (user_id, rec_id))
        result = cursor.fetchone()
        conn.commit()
        
        if not result:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {"success": True, "data": result}

# ============================================================================
# ACTIONS ENDPOINTS 
# ============================================================================

@app.post("/api/actions", status_code=status.HTTP_201_CREATED)
def create_action(action: ActionCreate):
    """Log an action taken on a recommendation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO actions (user_id, recommendation_id, action_taken, result)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """, (action.user_id, action.recommendation_id, action.action_taken, action.result))
        result = cursor.fetchone()
        
        # Auto-update recommendation status to 'acted' if not already
        if action.recommendation_id:
            cursor.execute("""
                UPDATE recommendations 
                SET status = 'acted'
                WHERE id = %s AND status = 'pending'
            """, (action.recommendation_id,))
        
        conn.commit()
        return {"success": True, "data": result}

@app.get("/api/recommendations/{rec_id}/actions")
def get_recommendation_actions(rec_id: int):
    """Get all actions taken on a recommendation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, 
                   u.first_name || ' ' || COALESCE(u.second_name, '') as user_name,
                   u.email as user_email
            FROM actions a
            JOIN users u ON u.id = a.user_id
            WHERE a.recommendation_id = %s
            ORDER BY a.taken_at DESC
        """, (rec_id,))
        return {"success": True, "data": cursor.fetchall()}

@app.get("/api/users/{user_id}/actions")
def get_user_actions(user_id: int, limit: int = 50):
    """Get all actions taken by a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, 
                   r.title as recommendation_title,
                   r.confidence as recommendation_confidence
            FROM actions a
            LEFT JOIN recommendations r ON r.id = a.recommendation_id
            WHERE a.user_id = %s
            ORDER BY a.taken_at DESC
            LIMIT %s
        """, (user_id, limit))
        return {"success": True, "data": cursor.fetchall()}