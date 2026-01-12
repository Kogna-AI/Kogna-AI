from fastapi import APIRouter, HTTPException, status, Depends
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
from uuid import UUID
from datetime import datetime

from core.permissions import UserContext, get_user_context
from routers.auth import _validate_password_strength, ph

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
def list_organization_teams(org_id: str, db=Depends(get_db)):
    """List all teams in an organization with member count."""
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
    """Create an invitation for a specific team (manager or above).

    Returns minimal data including the generated token so the frontend can
    construct an invitation URL and (for now) share it manually or via email.
    """
    if not user_ctx.is_manager():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers or above can invite team members",
        )

    email = invitation.email.strip().lower()

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Ensure team belongs to the same organization as the inviter
        cursor.execute(
            "SELECT id, organization_id, name FROM teams WHERE id = %s",
            (str(team_id),),
        )
        team_row = cursor.fetchone()
        if not team_row:
            raise HTTPException(status_code=404, detail="Team not found")

        if str(team_row["organization_id"]) != str(user_ctx.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot invite to a team in a different organization",
            )

        # Create invitation
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
            RETURNING id, email, token, expires_at
            """,
            (
                team_row["organization_id"],
                str(team_id),
                email,
                invitation.role or "member",
                user_ctx.id,
            ),
        )
        inv = cursor.fetchone()
        conn.commit()

    return {"success": True, "data": inv}


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

        # Look up and validate invitation
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
                %s,
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
                inv["role"] or "member",
                email,
                hashed_password,
            ),
        )
        user_row = cursor.fetchone()
        user_id = user_row["id"]

        # Add to team_members
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
            (inv["team_id"], user_id, inv["role"] or "member"),
        )

        # Mark invitation as accepted
        cursor.execute(
            """
            UPDATE team_invitations
            SET status = 'accepted',
                accepted_user_id = %s,
                accepted_at = NOW()
            WHERE id = %s
            """,
            (user_id, inv["id"]),
        )

        conn.commit()

    return {
        "success": True,
        "data": {
            "user_id": str(user_id),
            "organization_id": str(inv["organization_id"]),
            "team_id": str(inv["team_id"]),
        },
    }
