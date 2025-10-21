from fastapi import APIRouter, HTTPException, status
from core.database import get_db
from core.models import TeamCreate, TeamMemberAdd
import psycopg2

router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate):
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

@router.post("/members")
def add_team_member(member: TeamMemberAdd):
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
