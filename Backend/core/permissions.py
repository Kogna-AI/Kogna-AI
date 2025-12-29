"""
Permission Middleware for RBAC (Role-Based Access Control)
Connects user_id with roles/permissions to secure AI agents and data access.
"""

import os
from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from auth.dependencies import get_current_user
from core.database import get_db
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================
# USER CONTEXT CLASS
# ============================================

#Enhanced user context that includes role and permission information. This is passed to AI agents to filter data based on user's access level.
class UserContext:
    def __init__(
        self,
        id: str,                          # Internal user ID from users table
        supabase_id: str,                 # Supabase auth user ID
        email: str,
        organization_id: Optional[str],
        first_name: Optional[str],
        second_name: Optional[str],
        role_name: Optional[str],         # e.g., 'executive', 'manager', 'analyst'
        role_level: int,                  # Hierarchy: 1=viewer, 2=analyst, 3=manager, 4=executive
        permissions: List[str],           # e.g., ['agents:invoke', 'insights:read:organization']
        team_ids: List[str]               # Teams user belongs to
    ):
        self.id = id
        self.supabase_id = supabase_id
        self.email = email
        self.organization_id = organization_id
        self.first_name = first_name
        self.second_name = second_name
        self.role_name = role_name
        self.role_level = role_level
        self.permissions = permissions
        self.team_ids = team_ids

    # this checks if user has a specific permission.
    def has_permission(self, resource: str, action: str, scope: str = None) -> bool:
        """
        Args:
            resource: 'agents', 'insights', 'objectives', etc.
            action: 'read', 'write', 'invoke', etc.
            scope: 'own', 'team', 'organization' (optional)

        Returns:
            True if user has the permission, False otherwise.
        """
        if scope:
            permission_string = f"{resource}:{action}:{scope}"
        else:
            # Check if user has ANY scope for this resource:action
            permission_prefix = f"{resource}:{action}:"
            return any(p.startswith(permission_prefix) for p in self.permissions)

        return permission_string in self.permissions

    def is_executive(self) -> bool:
        """Check if user is executive level (level 4+)"""
        return self.role_level >= 4

    def is_manager(self) -> bool:
        """Check if user is manager level (level 3+)"""
        return self.role_level >= 3

    def is_analyst(self) -> bool:
        """Check if user is analyst level (level 2+)"""
        return self.role_level >= 2

    def can_access_organization_data(self) -> bool:
        """Check if user can access full organization data"""
        return self.role_level >= 3  # Managers and above

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "id": self.id,
            "email": self.email,
            "organization_id": self.organization_id,
            "role_name": self.role_name,
            "role_level": self.role_level,
            "permissions": self.permissions,
            "team_ids": self.team_ids
        }


# ============================================
# CORE PERMISSION FUNCTIONS
# ============================================

#this fetch user from users table by their Supabase auth ID.
def get_user_from_supabase_id(supabase_id: str) -> Optional[Dict[str, Any]]:
    """
    Args:
        supabase_id: The Supabase auth user ID (from auth.users)

    Returns:
        User dictionary or None if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, supabase_id, organization_id, first_name, second_name, email
            FROM users
            WHERE supabase_id = %s
        """, (supabase_id,))
        return cursor.fetchone()

#this function will fetch user's role, role level, and all permissions.
def get_user_role_and_permissions(user_id: str) -> Dict[str, Any]:
    """
    Args:
        user_id: Internal user ID from users table

    Returns:
        Dict with role_name, role_level, and permissions list
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get role information
        cursor.execute("""
            SELECT r.name, r.level
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = %s
            LIMIT 1
        """, (user_id,))
        role_data = cursor.fetchone()

        if not role_data:
            # Default to viewer if no role assigned
            return {
                "role_name": "viewer",
                "role_level": 1,
                "permissions": []
            }

        # Get all permissions for this role
        cursor.execute("""
            SELECT p.resource, p.action, p.scope
            FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = %s
        """, (user_id,))
        permissions_data = cursor.fetchall()

        # Format permissions as 'resource:action:scope'
        permissions = [
            f"{perm['resource']}:{perm['action']}:{perm['scope']}"
            for perm in permissions_data
        ]

        return {
            "role_name": role_data['name'],
            "role_level": role_data['level'],
            "permissions": permissions
        }


#this will set list of team IDs the user belongs to.
def get_user_teams(user_id: str) -> List[str]:
    """
    Args:
        user_id: Internal user ID from users table

    Returns:
        List of team IDs
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT team_id
            FROM team_members
            WHERE user_id = %s
        """, (user_id,))
        teams = cursor.fetchall()
        return [str(team['team_id']) for team in teams]

#Build complete UserContext from JWT user data. This is the main function that connects authentication with RBAC.
def build_user_context(jwt_user: dict) -> UserContext:
    """
    Args:
        jwt_user: User dict from JWT token with 'id', 'email', 'organization_id'

    Returns:
        UserContext with full role and permission information

    Raises:
        HTTPException: If user not found in database
    """
    user_id = jwt_user["id"]
    
    # Get user from database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, organization_id, first_name, second_name, email
            FROM users
            WHERE id = %s
        """, (user_id,))
        db_user = cursor.fetchone()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {user_id} not found in database."
        )

    # Get role and permissions
    role_data = get_user_role_and_permissions(user_id)

    # Get teams
    team_ids = get_user_teams(user_id)

    # Build context
    return UserContext(
        id=str(user_id),
        supabase_id=None,  # Not used, keeping for backward compatibility
        email=jwt_user["email"],
        organization_id=str(db_user['organization_id']) if db_user['organization_id'] else None,
        first_name=db_user.get('first_name'),
        second_name=db_user.get('second_name'),
        role_name=role_data['role_name'],
        role_level=role_data['role_level'],
        permissions=role_data['permissions'],
        team_ids=team_ids
    )


# ============================================
# FASTAPI DEPENDENCY FUNCTIONS
# ============================================


# FastAPI dependency to get full user context with roles/permissions. Use this in endpoints that need to know user's role.
async def get_user_context(user = Depends(get_current_user)) -> UserContext:
    """
    Example:
        @router.get("/data")
        async def get_data(user_ctx: UserContext = Depends(get_user_context)):
            if user_ctx.is_executive():
                # Return all data
            else:
                # Return filtered data
    """
    return build_user_context(user)


#this factory function to create a dependency that requires a specific permission.
def require_permission(resource: str, action: str, scope: str = None):
    """
    Args:
        resource: 'agents', 'insights', 'objectives', etc.
        action: 'read', 'write', 'invoke', etc.
        scope: 'own', 'team', 'organization' (optional)

    Returns:
        FastAPI dependency function that checks permission
    """
    async def permission_checker(user_ctx: UserContext = Depends(get_user_context)) -> UserContext:
        if not user_ctx.has_permission(resource, action, scope):
            permission_str = f"{resource}:{action}:{scope}" if scope else f"{resource}:{action}"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission_str}. "
                       f"Your role '{user_ctx.role_name}' does not have access to this resource."
            )
        return user_ctx

    return permission_checker

# Factory function to create a dependency that requires minimum role level.
def require_role_level(min_level: int, role_name: str = None):
    """
    Args:
        min_level: Minimum role level (1=viewer, 2=analyst, 3=manager, 4=executive, 5=admin)
        role_name: Optional friendly name for error message

    Returns:
        FastAPI dependency function that checks role level

    """
    async def role_checker(user_ctx: UserContext = Depends(get_user_context)) -> UserContext:
        if user_ctx.role_level < min_level:
            role_display = role_name or f"level {min_level}"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {role_display} role or higher. "
                       f"Your role: {user_ctx.role_name} (level {user_ctx.role_level})"
            )
        return user_ctx

    return role_checker

# Dependency to ensure user has organization-wide data access. Useful for dashboards that show org-level KPIs.
def require_organization_access(user_ctx: UserContext = Depends(get_user_context)) -> UserContext:
    """
    Example:
        @router.get("/org/kpis")
        async def get_org_kpis(user_ctx = Depends(require_organization_access)):
            # Only managers and executives can access
    """
    if not user_ctx.can_access_organization_data():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This endpoint requires organization-wide access. "
                   f"Your role '{user_ctx.role_name}' only has team-level access."
        )
    return user_ctx


# ============================================
# AUDIT LOGGING
# ============================================

def log_audit(
    user_ctx: UserContext,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    query: str = None,
    results_count: int = None,
    execution_time_ms: int = None,
    ip_address: str = None
):
    """
    Log user action to audit_logs table.

    Args:
        user_ctx: User context
        action: Action performed (e.g., 'agent:invoked', 'kpi:extracted')
        resource_type: Type of resource accessed
        resource_id: ID of resource
        query: User's query (for AI agents)
        results_count: Number of records returned
        execution_time_ms: How long the operation took
        ip_address: User's IP address
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (
                    user_id, organization_id, action, resource_type, resource_id,
                    query, results_count, execution_time_ms, ip_address
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_ctx.id,
                user_ctx.organization_id,
                action,
                resource_type,
                resource_id,
                query,
                results_count,
                execution_time_ms,
                ip_address
            ))
            conn.commit()
    except Exception as e:
        # Don't fail the request if audit logging fails
        print(f"Audit logging failed: {e}")


# ============================================
# HELPER FUNCTIONS FOR AI AGENTS
# ============================================

#Filter objectives list based on user's role.Executives see all, managers see all, team members see only their team's.
def filter_objectives_by_role(objectives: List[Dict], user_ctx: UserContext) -> List[Dict]:
    """
    Args:
        objectives: List of objective dictionaries
        user_ctx: User context with role information

    Returns:
        Filtered list of objectives
    """
    if user_ctx.is_manager():
        # Managers and executives see all
        return objectives

    # Filter to only user's teams
    return [
        obj for obj in objectives
        if obj.get('team_responsible') in user_ctx.team_ids
    ]

#this will filter metrics/KPIs based on user's role.
def filter_metrics_by_role(metrics: List[Dict], user_ctx: UserContext) -> List[Dict]:
    """
    Args:
        metrics: List of metric dictionaries
        user_ctx: User context with role information

    Returns:
        Filtered list of metrics
    """
    if user_ctx.is_manager():
        # Managers and executives see all org metrics
        return metrics

    # Team members might see limited metrics
    # (implement team-level filtering if metrics have team_id)
    return metrics

#Get the data scope configuration for AI agents based on user role. This is passed to AI agents to filter their queries.
def get_user_data_scope(user_ctx: UserContext) -> Dict[str, Any]:
    """
    Returns:
        Dict with scope configuration:
        {
            "scope": "organization" | "team" | "own",
            "organization_id": "...",
            "team_ids": [...],
            "user_id": "..."
        }
    """
    if user_ctx.is_executive():
        scope = "organization"
    elif user_ctx.is_manager():
        scope = "organization"  # Managers see org data
    elif user_ctx.team_ids:
        scope = "team"
    else:
        scope = "own"

    return {
        "scope": scope,
        "organization_id": user_ctx.organization_id,
        "team_ids": user_ctx.team_ids,
        "user_id": user_ctx.id,
        "role_level": user_ctx.role_level
    }
