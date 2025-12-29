from fastapi import APIRouter, HTTPException, status, Depends
from core.database import get_db
from core.models import TeamCreate, TeamMemberAdd
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import UUID

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
