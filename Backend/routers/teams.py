from fastapi import APIRouter, HTTPException, status, Depends, Query
from core.database import get_db
from core.models import (
    TeamCreate,
    TeamMemberAdd,
    TeamInvitationCreate,
    TeamInvitationMeta,
    AcceptInvitationRequest,
)
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import UUID, uuid4
from datetime import datetime

from core.permissions import UserContext, get_user_context
from routers.auth import _validate_password_strength, ph
import logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate, db=Depends(get_db)):
    """Create a team for an organization."""
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO teams (organization_id, name)
            VALUES (%s, %s)
            RETURNING *
            """,
            (team.organization_id, team.name),
        )
        result = cursor.fetchone()
    return {"success": True, "data": result}


@router.post("/members")
def add_team_member(member: TeamMemberAdd, db=Depends(get_db)):
    """Add a user to a team."""
    with db as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO team_members (team_id, user_id, role, performance, capacity, status)
                VALUES (%s, %s, %s, %s, %s, 'available')
                RETURNING *
                """,
                (member.team_id, member.user_id, member.role, member.performance, member.capacity),
            )
            result = cursor.fetchone()
            return {"success": True, "data": result}
        except psycopg2.IntegrityError:
            raise HTTPException(status_code=400, detail="User already in team")


@router.get("/{team_id}/members")
def get_team_members(team_id: UUID, db=Depends(get_db)):
    """Get all members for a team."""
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT tm.*, u.first_name, u.second_name, u.email, u.role as user_role
            FROM team_members tm
            JOIN users u ON u.id = tm.user_id
            WHERE tm.team_id = %s
            """,
            (str(team_id),),
        )
        members = cursor.fetchall()
    return {"success": True, "data": members}


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    user_ctx: UserContext = Depends(get_user_context),
    db=Depends(get_db),
):
    """Remove a user from a team (manager or above within same organization)."""

    if not user_ctx.is_manager():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers or above can remove team members",
        )

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Ensure team belongs to the same organization as the acting user
        cursor.execute(
            "SELECT id, organization_id FROM teams WHERE id = %s",
            (str(team_id),),
        )
        team_row = cursor.fetchone()
        if not team_row:
            raise HTTPException(status_code=404, detail="Team not found")

        if str(team_row["organization_id"]) != str(user_ctx.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify a team in a different organization",
            )

        # Check membership
        cursor.execute(
            """
            SELECT id FROM team_members
            WHERE team_id = %s AND user_id = %s
            """,
            (str(team_id), str(user_id)),
        )
        membership = cursor.fetchone()
        if not membership:
            raise HTTPException(status_code=404, detail="User is not in this team")

        # Remove membership
        cursor.execute(
            "DELETE FROM team_members WHERE id = %s",
            (membership["id"],),
        )
        conn.commit()

    return {"success": True}


@router.get("/hierarchy")
def get_team_hierarchy(
    user_ctx: UserContext = Depends(get_user_context),
    db=Depends(get_db),
):
    """Return a hierarchical view of teams and users based on RBAC.

    Hierarchy structure (based on actual roles table):
    - CEO/Executive (level 4-5): sees all Directors (level 3)
    - Directors (level 3): see their supervised teams with team leaders (level 2) on hover
    - Team Leaders (level 2): see all members in their team
    """
    organization_id = user_ctx.organization_id
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization",
        )

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Determine hierarchy mode from role level
        # Level 5 = Admin, Level 4 = Executive, Level 3 = Director, Level 2 = Team Leader
        if user_ctx.role_level >= 4:
            mode = "ceo"
        elif user_ctx.role_level >= 3:
            mode = "director"
        elif user_ctx.role_level >= 2:
            mode = "manager"
        else:
            mode = "member"

        # Fetch current user basic info
        cursor.execute(
            """
            SELECT id, first_name, second_name, role AS title, email
            FROM users
            WHERE id = %s AND organization_id = %s
            """,
            (user_ctx.id, organization_id),
        )
        self_row = cursor.fetchone()
        if not self_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current user not found in organization",
            )

        self_member = {
            "id": str(self_row["id"]),
            "first_name": self_row.get("first_name"),
            "second_name": self_row.get("second_name"),
            "title": self_row.get("title"),
            "rbac_role_name": user_ctx.role_name,
            "rbac_role_level": user_ctx.role_level,
        }

        # CEO Mode: Return all Directors (level 3) with their teams
        if mode == "ceo":
            # Get all directors (level 3)
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.first_name,
                    u.second_name,
                    u.role AS title,
                    u.email,
                    r.name AS rbac_role_name,
                    r.level AS rbac_role_level
                FROM users u
                JOIN user_roles ur ON ur.user_id = u.id
                JOIN roles r ON r.id = ur.role_id
                WHERE u.organization_id = %s AND r.level = 3
                """,
                (organization_id,),
            )
            director_rows = cursor.fetchall()

            directors = []
            for dir_row in director_rows:
                director_id = str(dir_row["id"])
                
                # Get teams supervised by this director
                # A director supervises teams where they are a member
                cursor.execute(
                    """
                    SELECT DISTINCT
                    t.id AS team_id,
                        t.name AS team_name
                    FROM teams t
                    JOIN team_members tm ON t.id = tm.team_id
                    WHERE tm.user_id = %s AND t.organization_id = %s
                    """,
                    (director_id, organization_id),
                )
                supervised_teams = cursor.fetchall()

                # For each team, get team leaders (level 3) and members
                teams_with_details = []
                for team_row in supervised_teams:
                    team_id = str(team_row["team_id"])
                    
                    # Get team leaders (level 2) in this team
                    cursor.execute(
                        """
                        SELECT
                            u.id,
                    u.first_name,
                    u.second_name,
                    u.role AS user_title,
                    r.name AS rbac_role_name,
                    r.level AS rbac_role_level
                        FROM team_members tm
                        JOIN users u ON u.id = tm.user_id
                        JOIN user_roles ur ON ur.user_id = u.id
                        JOIN roles r ON r.id = ur.role_id
                        WHERE tm.team_id = %s AND r.level = 2
                        """,
                        (team_id,),
                    )
                    leaders = cursor.fetchall()

                    # Get all members in this team (for metrics calculation)
                    # Exclude directors (level 3) and above from the count
                    cursor.execute(
                        """
                        SELECT
                            u.id,
                            tm.performance,
                            tm.capacity,
                            tm.project_count
                        FROM team_members tm
                        JOIN users u ON u.id = tm.user_id
                        LEFT JOIN user_roles ur ON ur.user_id = u.id
                        LEFT JOIN roles r ON r.id = ur.role_id
                        WHERE tm.team_id = %s
                        AND (r.level IS NULL OR r.level < 3)
                        """,
                        (team_id,),
                    )
                    all_members = cursor.fetchall()

                    # For director-supervised teams, members list should only show team leaders (level 2)
                    # Exclude directors (level 3) and other roles
                    team_leaders_only = [
                        {
                            "id": str(l["id"]),
                            "first_name": l.get("first_name"),
                            "second_name": l.get("second_name"),
                            "title": l.get("user_title"),
                            "rbac_role_name": l.get("rbac_role_name"),
                            "rbac_role_level": l.get("rbac_role_level"),
                            "performance": None,  # Performance not shown for leaders in this view
                            "capacity": None,
                            "project_count": None,
                            "status": "available",
                        }
                        for l in leaders
                    ]

                    teams_with_details.append({
                        "id": team_id,
                        "name": team_row["team_name"],
                        "leaders": [
                            {
                                "id": str(l["id"]),
                                "first_name": l.get("first_name"),
                                "second_name": l.get("second_name"),
                                "title": l.get("user_title"),
                                "rbac_role_name": l.get("rbac_role_name"),
                                "rbac_role_level": l.get("rbac_role_level"),
                            }
                            for l in leaders
                        ],
                        "members": team_leaders_only,  # Only team leaders (level 2), excluding directors
                        "metrics": {
                            "member_count": len(all_members),
                            "avg_performance": round(
                                sum(m.get("performance", 0) or 0 for m in all_members if m.get("performance"))
                                / max(len([m for m in all_members if m.get("performance")]), 1)
                            ) if any(m.get("performance") for m in all_members) else None,
                            "avg_capacity": round(
                                sum(m.get("capacity", 0) or 0 for m in all_members if m.get("capacity"))
                                / max(len([m for m in all_members if m.get("capacity")]), 1)
                            ) if any(m.get("capacity") for m in all_members) else None,
                        },
                    })

                directors.append({
                    "id": director_id,
                    "first_name": dir_row.get("first_name"),
                    "second_name": dir_row.get("second_name"),
                    "title": dir_row.get("title"),
                    "rbac_role_name": dir_row.get("rbac_role_name"),
                    "rbac_role_level": dir_row.get("rbac_role_level"),
                    "teams": teams_with_details,
                })

            return {
                "success": True,
                "data": {
                    "mode": mode,
                    "organization_id": str(organization_id),
                    "directors": directors,
                    "teams": [],
                    "self_member": self_member,
                },
            }

        # Director Mode: Return teams supervised by this director
        elif mode == "director":
            # Get teams where this director is a member
            cursor.execute(
                """
                SELECT DISTINCT
                    t.id AS team_id,
                    t.name AS team_name
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.user_id = %s AND t.organization_id = %s
                """,
                (user_ctx.id, organization_id),
            )
            supervised_teams = cursor.fetchall()

            teams_with_details = []
            for team_row in supervised_teams:
                team_id = str(team_row["team_id"])
                
                # Get team leaders (level 2) in this team
                cursor.execute(
                    """
                    SELECT
                        u.id,
                        u.first_name,
                        u.second_name,
                        u.role AS user_title,
                        r.name AS rbac_role_name,
                        r.level AS rbac_role_level
                    FROM team_members tm
                    JOIN users u ON u.id = tm.user_id
                    JOIN user_roles ur ON ur.user_id = u.id
                    JOIN roles r ON r.id = ur.role_id
                    WHERE tm.team_id = %s AND r.level = 2
                    """,
                    (team_id,),
                )
                leaders = cursor.fetchall()

                # Get all members for metrics calculation
                # Exclude directors (level 3) and above from the count
                cursor.execute(
                    """
                    SELECT
                        u.id,
                        tm.performance,
                        tm.capacity,
                        tm.project_count
                    FROM team_members tm
                    JOIN users u ON u.id = tm.user_id
                    LEFT JOIN user_roles ur ON ur.user_id = u.id
                    LEFT JOIN roles r ON r.id = ur.role_id
                    WHERE tm.team_id = %s
                    AND (r.level IS NULL OR r.level < 3)
                    """,
                    (team_id,),
                )
                all_members = cursor.fetchall()

                # For director-supervised teams, members list should only show team leaders (level 2)
                # Exclude directors (level 3) and other roles
                team_leaders_only = [
                    {
                        "id": str(l["id"]),
                        "first_name": l.get("first_name"),
                        "second_name": l.get("second_name"),
                        "title": l.get("user_title"),
                        "rbac_role_name": l.get("rbac_role_name"),
                        "rbac_role_level": l.get("rbac_role_level"),
                        "performance": None,  # Performance not shown for leaders in this view
                        "capacity": None,
                        "project_count": None,
                        "status": "available",
                    }
                    for l in leaders
                ]

                teams_with_details.append({
                    "id": team_id,
                    "name": team_row["team_name"],
                    "leaders": [
                        {
                            "id": str(l["id"]),
                            "first_name": l.get("first_name"),
                            "second_name": l.get("second_name"),
                            "title": l.get("user_title"),
                            "rbac_role_name": l.get("rbac_role_name"),
                            "rbac_role_level": l.get("rbac_role_level"),
                        }
                        for l in leaders
                    ],
                    "members": team_leaders_only,  # Only team leaders (level 3), excluding directors
                    "metrics": {
                        "member_count": len(all_members),
                        "avg_performance": round(
                            sum(m.get("performance", 0) or 0 for m in all_members if m.get("performance"))
                            / max(len([m for m in all_members if m.get("performance")]), 1)
                        ) if any(m.get("performance") for m in all_members) else None,
                        "avg_capacity": round(
                            sum(m.get("capacity", 0) or 0 for m in all_members if m.get("capacity"))
                            / max(len([m for m in all_members if m.get("capacity")]), 1)
                        ) if any(m.get("capacity") for m in all_members) else None,
                    },
                })

            return {
                "success": True,
                "data": {
                    "mode": mode,
                    "organization_id": str(organization_id),
                    "directors": [],
                    "teams": teams_with_details,
                    "self_member": self_member,
                },
            }

        # Manager/Team Leader Mode: Return all members in their team
        elif mode == "manager":
            # Get teams where this manager is a member
            accessible_team_ids = [str(tid) for tid in (user_ctx.team_ids or [])]
            
            if not accessible_team_ids:
                return {
                    "success": True,
                    "data": {
                        "mode": mode,
                        "organization_id": str(organization_id),
                        "directors": [],
                        "teams": [],
                        "self_member": self_member,
                    },
                }

            teams_with_details = []
            for team_id in accessible_team_ids:
                # Get team info
                cursor.execute(
                    """
                    SELECT id, name
                    FROM teams
                    WHERE id = %s AND organization_id = %s
                    """,
                    (team_id, organization_id),
                )
                team_row = cursor.fetchone()
                if not team_row:
                    continue

                # Get all members in this team
                cursor.execute(
                    """
                    SELECT
                        u.id,
                        u.first_name,
                        u.second_name,
                        u.role AS user_title,
                        tm.performance,
                        tm.capacity,
                        tm.project_count,
                        tm.status,
                        r.name AS rbac_role_name,
                        r.level AS rbac_role_level
                    FROM team_members tm
                    JOIN users u ON u.id = tm.user_id
                    LEFT JOIN user_roles ur ON ur.user_id = u.id
                    LEFT JOIN roles r ON r.id = ur.role_id
                    WHERE tm.team_id = %s
                    """,
                    (team_id,),
                )
                all_members = cursor.fetchall()

                teams_with_details.append({
                    "id": team_id,
                    "name": team_row["name"],
                    "leaders": [],
                    "members": [
                        {
                            "id": str(m["id"]),
                            "first_name": m.get("first_name"),
                            "second_name": m.get("second_name"),
                            "title": m.get("user_title"),
                            "rbac_role_name": m.get("rbac_role_name") or "viewer",
                            "rbac_role_level": m.get("rbac_role_level") or 1,
                            "performance": m.get("performance"),
                            "capacity": m.get("capacity"),
                            "project_count": m.get("project_count"),
                            "status": m.get("status") or "available",
                        }
                        for m in all_members
                    ],
                    "metrics": {
                        "member_count": len(all_members),
                        "avg_performance": round(
                            sum(m.get("performance", 0) or 0 for m in all_members if m.get("performance"))
                            / max(len([m for m in all_members if m.get("performance")]), 1)
                        ) if any(m.get("performance") for m in all_members) else None,
                        "avg_capacity": round(
                            sum(m.get("capacity", 0) or 0 for m in all_members if m.get("capacity"))
                            / max(len([m for m in all_members if m.get("capacity")]), 1)
                        ) if any(m.get("capacity") for m in all_members) else None,
                    },
                })

            return {
                "success": True,
                "data": {
                    "mode": mode,
                    "organization_id": str(organization_id),
                    "directors": [],
                    "teams": teams_with_details,
                    "self_member": self_member,
                },
            }

        # Member Mode: Return only self
        else:
            return {
                "success": True,
                "data": {
                    "mode": mode,
                    "organization_id": str(organization_id),
                    "directors": [],
                    "teams": [],
                    "self_member": self_member,
                },
            }


@router.get("/{team_id}")
def get_team(team_id: UUID, db=Depends(get_db)):
    """Get a team by ID."""
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM teams WHERE id = %s", (str(team_id),))
        result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"success": True, "data": result}


@router.get("/user/{user_id}")
def get_user_team(user_id: str, db=Depends(get_db)):
    """Get the first team that a user belongs to."""
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT t.*
            FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE tm.user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="User is not a member of any team")
    return {"success": True, "data": result}


@router.get("/organization/{org_id}")
def list_organization_teams(
    org_id: str,
    exclude_ceo_teams: bool = Query(False, description="Exclude teams that contain CEOs (level 5 users)"),
    user_ctx: UserContext = Depends(get_user_context),
    db=Depends(get_db),
):
    """List all teams in an organization with member count.
    
    Args:
        exclude_ceo_teams: If True, exclude teams that contain CEOs (level 5 users).
                          Useful when selecting teams for director supervision.
    """
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if exclude_ceo_teams:
            # Exclude teams that have CEOs (level 5 users) or any executives with level >= 5
            # Use NOT EXISTS for better performance and to handle NULLs correctly
            cursor.execute(
                """
                SELECT 
                    t.*,
                    COUNT(tm.id) as member_count,
                    AVG(tm.performance) as avg_performance
                FROM teams t
                LEFT JOIN team_members tm ON t.id = tm.team_id
                WHERE t.organization_id = %s
                AND NOT EXISTS (
                    SELECT 1
                    FROM team_members tm2
                    JOIN users u ON u.id = tm2.user_id
                    JOIN user_roles ur ON ur.user_id = u.id
                    JOIN roles r ON r.id = ur.role_id
                    WHERE tm2.team_id = t.id
                    AND r.level >= 5
                    AND u.organization_id = %s
                )
                GROUP BY t.id
                ORDER BY t.created_at DESC
                """,
                (org_id, org_id),
            )
        else:
            cursor.execute(
                """
                SELECT 
                    t.*,
                    COUNT(tm.id) as member_count,
                    AVG(tm.performance) as avg_performance
                FROM teams t
                LEFT JOIN team_members tm ON t.id = tm.team_id
                WHERE t.organization_id = %s
                GROUP BY t.id
                ORDER BY t.created_at DESC
                """,
                (org_id,),
            )
        results = cursor.fetchall()
    return {"success": True, "data": results}


@router.post("/{team_id}/invitations", status_code=status.HTTP_201_CREATED)
def create_team_invitation(
    team_id: UUID,
    invitation: TeamInvitationCreate,
    user_ctx: UserContext = Depends(get_user_context),
    db=Depends(get_db),
):
    """Create an invitation for a specific team (team leaders and above).
    
    For directors: if team_ids is provided, creates invitations for multiple teams.
    Otherwise, uses the team_id from the path parameter.

    Role assignment rules (enforced server-side):
    - CEO / Executives (role_level >= 4): can invite directors, managers, or members.
    - Directors (role_level >= 3): can invite managers or members.
    - Team leaders/managers (role_level >= 2): can invite members only.
    """
    # Require at least team-leader level to invite
    if user_ctx.role_level < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team leaders or above can invite team members",
        )

    email = invitation.email.strip().lower()

    # Normalize requested role and enforce allowed set based on inviter level
    requested_role = (invitation.role or "member").lower()
    if user_ctx.role_level >= 4:
        allowed_roles = {"director", "manager", "member"}
    elif user_ctx.role_level >= 3:
        allowed_roles = {"manager", "member"}
    else:  # role_level == 2
        allowed_roles = {"member"}

    if requested_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to assign this role via invitation",
        )

    # For directors, allow multiple teams. For others, use single team from path.
    team_ids_to_invite = []
    if requested_role == "director" and invitation.team_ids and len(invitation.team_ids) > 0:
        # Director with multiple teams
        team_ids_to_invite = invitation.team_ids
        # Only CEO (level 5) can assign multiple teams to directors
        if user_ctx.role_level < 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only CEO can assign multiple teams to directors",
            )
    else:
        # Single team from path parameter
        team_ids_to_invite = [str(team_id)]

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Validate all teams belong to the same organization
        placeholders = ", ".join(["%s"] * len(team_ids_to_invite))
        cursor.execute(
            f"""
            SELECT id, organization_id, name 
            FROM teams 
            WHERE id IN ({placeholders})
            """,
            team_ids_to_invite,
        )
        team_rows = cursor.fetchall()

        if len(team_rows) != len(team_ids_to_invite):
            raise HTTPException(
                status_code=404,
                detail="One or more teams not found",
            )

        # Ensure all teams belong to the same organization as the inviter
        for team_row in team_rows:
            if str(team_row["organization_id"]) != str(user_ctx.organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot invite to teams in a different organization",
                )

        # For directors: validate that teams don't have CEOs (level 5 users)
        # Directors cannot supervise teams that contain CEOs
        if requested_role == "director":
            team_ids_placeholders = ", ".join(["%s"] * len(team_ids_to_invite))
            cursor.execute(
                f"""
                SELECT DISTINCT t.id, t.name, u.first_name, u.second_name
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                JOIN users u ON u.id = tm.user_id
                JOIN user_roles ur ON ur.user_id = u.id
                JOIN roles r ON r.id = ur.role_id
                WHERE t.id IN ({team_ids_placeholders})
                AND r.level = 5
                """,
                team_ids_to_invite,
            )
            teams_with_ceos = cursor.fetchall()
            
            if teams_with_ceos:
                team_names = [f"{t['name']}" for t in teams_with_ceos]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Directors cannot supervise teams that contain CEOs. The following teams have CEOs: {', '.join(team_names)}",
                )

        # Create invitations for all teams
        # For directors with multiple teams, we'll use the email to link them during acceptance
        # Each invitation gets a unique token (required by DB constraint)
        created_invitations = []
        for team_row in team_rows:
            cursor.execute(
                """
                INSERT INTO team_invitations (
                    organization_id,
                    team_id,
                    email,
                    role,
                    invited_by
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, email, token, expires_at, team_id
                """,
                (
                    team_row["organization_id"],
                    str(team_row["id"]),
                    email,
                    requested_role,
                    user_ctx.id,
                ),
            )
            inv = cursor.fetchone()
            created_invitations.append(inv)

        conn.commit()
        from utils.email_sender import EmailSender
        import os

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    # Use the token from the first created invitation
    invitation_url = f"{frontend_url}/accept-invitation?token={created_invitations[0]['token']}"

    # Fetch inviter name for personalization
    inviter_name = f"{user_ctx.first_name}" if hasattr(user_ctx, 'first_name') else "A team leader"

    try:
        EmailSender.send_email(
            to_email=email,
            subject=f"Invitation to join {team_rows[0]['name']} at {user_ctx.organization_name}", # Ensure org name is in context
            html_content=EmailSender.get_team_invitation_email_html(
                invitation_url=invitation_url,
                org_name="Your Organization", # Replace with actual org name lookup
                team_name=team_rows[0]["name"],
                inviter_name=inviter_name
            )
        )
        logger.info(f"Invitation email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")
    # Return the first invitation (they all share the same token)
    return {"success": True, "data": created_invitations[0] if created_invitations else None}


@router.get("/invitations/{token}", response_model=TeamInvitationMeta)
def get_team_invitation(token: UUID, db=Depends(get_db)):
    """Public endpoint to fetch minimal invitation metadata for signup UI."""
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT
                ti.email,
                o.name AS organization_name,
                t.name AS team_name,
                ti.status,
                ti.expires_at
            FROM team_invitations ti
            JOIN organizations o ON o.id = ti.organization_id
            JOIN teams t ON t.id = ti.team_id
            WHERE ti.token = %s
            """,
            (str(token),),
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if row["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invitation is not active")

    if row["expires_at"] and row["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation has expired")

    return TeamInvitationMeta(
        email=row["email"],
        organization_name=row["organization_name"],
        team_name=row["team_name"],
    )


@router.post("/invitations/{token}/accept")
def accept_team_invitation(
    token: UUID,
    payload: AcceptInvitationRequest,
    db=Depends(get_db),
):
    """Accept an invitation and create a user + team membership.

    This does not log the user in; it just provisions the account and membership.
    """
    _validate_password_strength(payload.password)

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Look up the invitation by token
        cursor.execute(
            """
            SELECT *
            FROM team_invitations
            WHERE token = %s
            FOR UPDATE
            """,
            (str(token),),
        )
        inv = cursor.fetchone()

        if not inv:
            raise HTTPException(status_code=404, detail="Invitation not found")

        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail="Invitation is not active")

        if inv["expires_at"] and inv["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invitation has expired")

        email = inv["email"].strip().lower()
        
        # For directors with multiple teams, find all pending invitations for this email
        # in the same organization (they were created together)
        # We're already in a transaction, so we don't need FOR UPDATE here
        cursor.execute(
            """
            SELECT *
            FROM team_invitations
            WHERE LOWER(email) = %s
            AND organization_id = %s
            AND status = 'pending'
            AND expires_at > NOW()
            ORDER BY created_at
            """,
            (email, inv["organization_id"]),
        )
        invitations = cursor.fetchall()
        
        # If no other invitations found, use just this one
        if not invitations:
            invitations = [inv]

        # Check for existing user with same email in this org
        cursor.execute(
            """
            SELECT id FROM users
            WHERE LOWER(email) = %s AND organization_id = %s
            """,
            (email, inv["organization_id"]),
        )
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists in the organization",
            )

        # Create user with Argon2-hashed password
        hashed_password = ph.hash(payload.password)

        # Map invitation role to RBAC role name
        # "director" -> "Director" (level 3)
        # "manager" -> "Team Leader" (level 2)
        # "member" -> "Team Member" (level 1)
        invited_role_name = (inv["role"] or "member").lower()
        rbac_role_name_map = {
            "director": "Director",
            "executive": "Executive",
            "manager": "Team Leader",
            "member": "Team Member",
        }
        rbac_role_name = rbac_role_name_map.get(invited_role_name, "Team Member")

        cursor.execute(
            """
            INSERT INTO users (
                id,
                organization_id,
                first_name,
                second_name,
                role,
                email,
                password_hash,
                supabase_id
            )
            VALUES (
                gen_random_uuid(),
                %s,
                %s,
                %s,
                NULL,
                %s,
                %s,
                gen_random_uuid()
            )
            RETURNING id
            """,
            (
                inv["organization_id"],
                payload.first_name,
                payload.second_name,
                email,
                hashed_password,
            ),
        )
        user_row = cursor.fetchone()
        user_id = user_row["id"]

        # Assign organization-level RBAC role based on invitation role
        # Always create user_roles entry for security
        cursor.execute(
            """
            SELECT id
            FROM roles
            WHERE name = %s
            LIMIT 1
            """,
            (rbac_role_name,),
        )
        rbac_role = cursor.fetchone()
        if rbac_role:
            cursor.execute(
                """
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
                """,
                (user_id, rbac_role["id"]),
            )
        else:
            # Fallback: if role not found, assign viewer role
            cursor.execute(
                """
                SELECT id FROM roles WHERE name = 'viewer' LIMIT 1
                """
            )
            viewer_role = cursor.fetchone()
            if viewer_role:
                cursor.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (%s, %s)
                    """,
                    (user_id, viewer_role["id"]),
                )

        # Add to team_members for all invited teams
        # For directors with multiple teams, add them to all teams
        team_ids_added = []
        for invitation in invitations:
            team_id = str(invitation["team_id"])
            # Check if user is already a member of this team
            cursor.execute(
                """
                SELECT id FROM team_members
                WHERE team_id = %s AND user_id = %s
                """,
                (team_id, user_id),
            )
            existing_membership = cursor.fetchone()
            
            if not existing_membership:
                cursor.execute(
                    """
                    INSERT INTO team_members (
                        id,
                        team_id,
                        user_id,
                        role,
                        performance,
                        capacity,
                        project_count,
                        status
                    )
                    VALUES (gen_random_uuid(), %s, %s, %s, 85, 80, 0, 'available')
                    """,
                    (team_id, user_id, rbac_role_name),
                )
                team_ids_added.append(team_id)

        # Mark all invitations as accepted
        invitation_ids = [str(inv["id"]) for inv in invitations]
        placeholders = ", ".join(["%s"] * len(invitation_ids))
        cursor.execute(
            f"""
            UPDATE team_invitations
            SET status = 'accepted',
                accepted_user_id = %s,
                accepted_at = NOW()
            WHERE id IN ({placeholders})
            """,
            [user_id] + invitation_ids,
        )

        conn.commit()

    return {
        "success": True,
        "data": {
            "user_id": str(user_id),
            "organization_id": str(inv["organization_id"]),
            "team_ids": [str(inv["team_id"]) for inv in invitations],
        },
    }
