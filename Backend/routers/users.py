"""
Users Router - Handles user management with Supabase authentication and RBAC
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from core.database import get_db
from core.models import UserUpdate, CreateUserRequest
from core.permissions import (
    get_user_context,
    UserContext,
    require_role_level,
    require_organization_access
)
import psycopg2
from psycopg2.extras import RealDictCursor
from auth.dependencies import get_current_user
router = APIRouter(prefix="/api/users", tags=["Users"])



# ============================================
# PUBLIC ENDPOINTS (No Auth Required)
# ============================================
@router.post("", status_code=201)
def create_user(data: CreateUserRequest, db=Depends(get_db)):
    """
    Create an internal team member.
    - No password
    - No supabase_id
    - Belongs to an existing organization
    """

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Organization must exist
        cursor.execute("SELECT id FROM organizations WHERE id = %s", (data.organization_id,))
        if not cursor.fetchone():
            raise HTTPException(404, "Organization not found")

        # 2. Insert internal team member
        cursor.execute("""
            INSERT INTO users (
                id,
                organization_id,
                first_name,
                second_name,
                role,
                email
            )
            VALUES (
                gen_random_uuid(),
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id, first_name, second_name, role, email
        """, (
            data.organization_id,
            data.first_name,
            data.second_name,
            data.role,
            data.email,
        ))

        new_user = cursor.fetchone()
        conn.commit()

        return {
            "success": True,
            "data": new_user
        }



@router.get("/by-supabase/{supabase_id}")
def get_user_by_supabase_id(supabase_id: str):
    """
    Get user by their Supabase authentication ID.

    This is used during login to fetch the internal user record
    after Supabase authentication succeeds.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, supabase_id, organization_id, first_name,
                   second_name, role, email, created_at
            FROM users
            WHERE supabase_id = %s
        """, (supabase_id,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found. Please ensure the user is registered in the database."
            )

        return {
            "success": True,
            "data": dict(user)
        }


# ============================================
# PROTECTED ENDPOINTS (Authentication Required)
# ============================================

@router.get("/me")
async def get_current_user(user_ctx: UserContext = Depends(get_user_context)):
    """
    Get the current authenticated user's information.

    This returns the full user profile with role and organization details.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.id,
                u.supabase_id,
                u.organization_id,
                u.first_name,
                u.second_name,
                u.role,
                u.email,
                u.created_at,
                o.name as organization_name
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = %s
        """, (user_ctx.id,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add RBAC information
        user_data = dict(user)
        user_data['rbac'] = {
            'role_name': user_ctx.role_name,
            'role_level': user_ctx.role_level,
            'permissions': user_ctx.permissions,
            'team_ids': user_ctx.team_ids
        }

        return {
            "success": True,
            "data": user_data
        }


@router.get("/visible")
async def list_visible_users(
    user_ctx: UserContext = Depends(get_user_context),
    limit: int = 100,
    offset: int = 0,
):
    """List people the current user can see (for TeamOverview).

    Rules:
    - Users with `users:read:organization` can see everyone in their organization.
    - Others see only members of their own teams.
      If they have no teams, they only see themselves.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        organization_id = user_ctx.organization_id
        has_org_permission = user_ctx.has_permission("users", "read", "organization")

        # Base query scoped to organization
        query = """
            SELECT
                u.id,
                u.supabase_id,
                u.organization_id,
                u.first_name,
                u.second_name,
                u.role,
                u.email,
                u.created_at,
                o.name as organization_name,
                COUNT(DISTINCT tm.team_id) as team_count
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            LEFT JOIN team_members tm ON u.id = tm.user_id
            WHERE u.organization_id = %s
        """
        params = [organization_id]

        # Restrict visibility for users without org-wide permission
        if not has_org_permission:
            if user_ctx.team_ids:
                # See only members who share at least one team
                team_ids_tuple = tuple(user_ctx.team_ids)
                placeholders = ", ".join(["%s"] * len(team_ids_tuple))
                query += f" AND tm.team_id IN ({placeholders})"
                params.extend(team_ids_tuple)
            else:
                # No teams: they only see themselves
                query += " AND u.id = %s"
                params.append(user_ctx.id)

        query += """
            GROUP BY u.id, o.name
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        users = cursor.fetchall()

        # Total count for pagination metadata, mirroring filters
        count_query = """
            SELECT COUNT(DISTINCT u.id) as count
            FROM users u
            LEFT JOIN team_members tm ON u.id = tm.user_id
            WHERE u.organization_id = %s
        """
        count_params = [organization_id]

        if not has_org_permission:
            if user_ctx.team_ids:
                team_ids_tuple = tuple(user_ctx.team_ids)
                placeholders = ", ".join(["%s"] * len(team_ids_tuple))
                count_query += f" AND tm.team_id IN ({placeholders})"
                count_params.extend(team_ids_tuple)
            else:
                count_query += " AND u.id = %s"
                count_params.append(user_ctx.id)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()["count"]

        return {
            "success": True,
            "data": [dict(user) for user in users],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
            },
        }


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    user_ctx: UserContext = Depends(get_user_context)
):
    """
    Get a specific user by ID.

    Access control:
    - Users can view their own profile
    - Managers can view users in their organization
    - Executives can view any user in their organization
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Fetch user
        cursor.execute("""
            SELECT
                u.id,
                u.supabase_id,
                u.organization_id,
                u.first_name,
                u.second_name,
                u.role,
                u.email,
                u.created_at,
                o.name as organization_name
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = %s
        """, (user_id,))

        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = dict(result)

        # Access control: Can only view users in same organization
        if user_data['organization_id'] != int(user_ctx.organization_id):
            raise HTTPException(
                status_code=403,
                detail="You can only view users in your own organization"
            )

        # Non-managers can only view their own profile
        if not user_ctx.is_manager() and user_id != int(user_ctx.id):
            raise HTTPException(
                status_code=403,
                detail="You can only view your own profile"
            )

        return {
            "success": True,
            "data": user_data
        }


@router.get("")
async def list_users(
    user_ctx: UserContext = Depends(require_organization_access),
    organization_id: Optional[int] = None,
    team_id: Optional[int] = None,
    role: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List users with optional filters.

    Requires: Manager role or higher

    Query Parameters:
    - organization_id: Filter by organization (defaults to user's org)
    - team_id: Filter by team
    - role: Filter by role
    - limit: Max results (default 100)
    - offset: Pagination offset (default 0)
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Default to user's organization
        if not organization_id:
            organization_id = int(user_ctx.organization_id)

        # Managers can only see their own organization
        if organization_id != int(user_ctx.organization_id):
            raise HTTPException(
                status_code=403,
                detail="You can only view users in your own organization"
            )

        # Build query with filters
        query = """
            SELECT
                u.id,
                u.supabase_id,
                u.organization_id,
                u.first_name,
                u.second_name,
                u.role,
                u.email,
                u.created_at,
                o.name as organization_name,
                COUNT(DISTINCT tm.team_id) as team_count
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            LEFT JOIN team_members tm ON u.id = tm.user_id
            WHERE u.organization_id = %s
        """

        params = [organization_id]

        # Add team filter
        if team_id:
            query += " AND tm.team_id = %s"
            params.append(team_id)

        # Add role filter
        if role:
            query += " AND u.role = %s"
            params.append(role)

        query += """
            GROUP BY u.id, o.name
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        users = cursor.fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) FROM users WHERE organization_id = %s"
        count_params = [organization_id]

        if role:
            count_query += " AND role = %s"
            count_params.append(role)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['count']

        return {
            "success": True,
            "data": [dict(user) for user in users],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total
            }
        }


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    updates: UserUpdate,
    user_ctx: UserContext = Depends(get_user_context)
):
    """
    Update user information.

    Access control:
    - Users can update their own profile (limited fields)
    - Managers can update users in their organization
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if user exists and get current data
        cursor.execute("""
            SELECT id, organization_id, role
            FROM users
            WHERE id = %s
        """, (user_id,))

        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Access control
        is_self = user_id == int(user_ctx.id)
        is_same_org = existing_user['organization_id'] == int(user_ctx.organization_id)

        if not is_same_org:
            raise HTTPException(
                status_code=403,
                detail="You can only update users in your own organization"
            )

        # Non-managers can only update themselves
        if not user_ctx.is_manager() and not is_self:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own profile"
            )

        # Non-managers cannot change their role or organization
        if not user_ctx.is_manager() and (updates.role or updates.organization_id):
            raise HTTPException(
                status_code=403,
                detail="You cannot change your role or organization"
            )

        # Build dynamic update query
        update_fields = []
        params = []

        if updates.first_name is not None:
            update_fields.append("first_name = %s")
            params.append(updates.first_name)

        if updates.second_name is not None:
            update_fields.append("second_name = %s")
            params.append(updates.second_name)

        if updates.email is not None:
            update_fields.append("email = %s")
            params.append(updates.email)

        if updates.role is not None and user_ctx.is_manager():
            update_fields.append("role = %s")
            params.append(updates.role)

        if updates.organization_id is not None and user_ctx.is_manager():
            update_fields.append("organization_id = %s")
            params.append(updates.organization_id)

        if not update_fields:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )

        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        # Execute update
        query = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, supabase_id, organization_id, first_name,
                      second_name, role, email, created_at, updated_at
        """
        params.append(user_id)

        try:
            cursor.execute(query, params)
            updated_user = cursor.fetchone()
            conn.commit()

            return {
                "success": True,
                "message": "User updated successfully",
                "data": dict(updated_user)
            }

        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Update failed: {str(e)}"
            )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    user_ctx: UserContext = Depends(require_role_level(3, "manager"))
):
    """
    Delete a user (soft delete by setting inactive).

    Requires: Manager role or higher
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("""
            SELECT id, organization_id
            FROM users
            WHERE id = %s
        """, (user_id,))

        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Can only delete users in same organization
        if existing_user['organization_id'] != int(user_ctx.organization_id):
            raise HTTPException(
                status_code=403,
                detail="You can only delete users in your own organization"
            )

        # Cannot delete yourself
        if user_id == int(user_ctx.id):
            raise HTTPException(
                status_code=400,
                detail="You cannot delete your own account"
            )

        # Soft delete (or hard delete - your choice)
        # Option 1: Soft delete (recommended)
        cursor.execute("""
            UPDATE users
            SET deleted_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (user_id,))

        # Option 2: Hard delete (uncomment if preferred)
        # cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

        conn.commit()

        return {
            "success": True,
            "message": "User deleted successfully"
        }


# ============================================
# USER STATISTICS & ADMIN ENDPOINTS
# ============================================

@router.get("/organization/{org_id}/stats")
async def get_organization_user_stats(
    org_id: int,
    user_ctx: UserContext = Depends(require_organization_access)
):
    """
    Get user statistics for an organization.

    Requires: Manager role or higher
    """
    # Verify user has access to this organization
    if org_id != int(user_ctx.organization_id):
        raise HTTPException(
            status_code=403,
            detail="You can only view statistics for your own organization"
        )

    with get_db() as conn:
        cursor = conn.cursor()

        # Get user counts by role
        cursor.execute("""
            SELECT
                role,
                COUNT(*) as count
            FROM users
            WHERE organization_id = %s
              AND deleted_at IS NULL
            GROUP BY role
            ORDER BY count DESC
        """, (org_id,))

        role_distribution = [dict(row) for row in cursor.fetchall()]

        # Get total users
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM users
            WHERE organization_id = %s
              AND deleted_at IS NULL
        """, (org_id,))

        total_users = cursor.fetchone()['total']

        # Get users by team
        cursor.execute("""
            SELECT
                t.name as team_name,
                COUNT(DISTINCT tm.user_id) as member_count
            FROM teams t
            LEFT JOIN team_members tm ON t.id = tm.team_id
            WHERE t.organization_id = %s
            GROUP BY t.id, t.name
            ORDER BY member_count DESC
        """, (org_id,))

        team_distribution = [dict(row) for row in cursor.fetchall()]

        # Get recent user activity (if you have audit logs)
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as new_users
            FROM users
            WHERE organization_id = %s
              AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (org_id,))

        recent_signups = [dict(row) for row in cursor.fetchall()]

        return {
            "success": True,
            "data": {
                "total_users": total_users,
                "role_distribution": role_distribution,
                "team_distribution": team_distribution,
                "recent_signups": recent_signups
            }
        }