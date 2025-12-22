from fastapi import APIRouter, HTTPException, status, Depends
from core.database import get_db
from core.models import TeamCreate, TeamMemberAdd
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import UUID

router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate, db=Depends(get_db)):
    with db as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO teams (organization_id, name)
                VALUES (%s, %s)
                RETURNING *
                """,
                (team.organization_id, team.name)
            )
            result = cursor.fetchone()

    return {"success": True, "data": result}


@router.post("/members")
def add_team_member(member: TeamMemberAdd, db=Depends(get_db)):
    try:
        with db as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO team_members (
                        team_id,
                        user_id,
                        role,
                        performance,
                        capacity,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, 'available')
                    RETURNING *
                    """,
                    (
                        str(member.team_id),
                        str(member.user_id),
                        member.role,
                        member.performance,
                        member.capacity,
                    )
                )
                result = cursor.fetchone()

        return {"success": True, "data": result}

    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="User already in team")

@router.get("/{team_id}/members")
def get_team_members(team_id: UUID, db=Depends(get_db)):
    with db as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    tm.*,
                    u.first_name,
                    u.second_name,
                    u.email,
                    u.role AS user_role
                FROM team_members tm
                JOIN users u ON u.id = tm.user_id
                WHERE tm.team_id = %s
                """,
                (str(team_id),)
            )
            members = cursor.fetchall()

    return {"success": True, "data": members}

@router.get("/{team_id}")
def get_team(team_id: UUID, db=Depends(get_db)):
    with db as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM teams WHERE id = %s",
                (str(team_id),)
            )
            team = cursor.fetchone()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return {"success": True, "data": team}

