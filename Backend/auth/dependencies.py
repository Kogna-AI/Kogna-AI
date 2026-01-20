from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from psycopg2.extras import RealDictCursor

from core.security import decode_access_token
from core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Reads the JWT and returns basic user identity.
    User ID is in the 'sub' claim.
    """
    payload = decode_access_token(token)
    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "organization_id": payload.get("organization_id"),
    }


async def get_backend_user_id(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Returns user_id, organization_id, and team context from JWT and database.
    Fetches user's team memberships to enable team-level RBAC filtering.
    """
    user_id = str(user["id"])
    organization_id = str(user["organization_id"])

    # Fetch user's team memberships
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT tm.team_id, tm.is_primary
            FROM team_members tm
            WHERE tm.user_id = %s
            ORDER BY tm.is_primary DESC, tm.joined_at ASC
        """, (user_id,))

        team_memberships = cursor.fetchall()

    team_ids = [str(tm["team_id"]) for tm in team_memberships]
    primary_team = next(
        (tm for tm in team_memberships if tm["is_primary"]),
        team_memberships[0] if team_memberships else None
    )

    return {
        "user_id": user_id,
        "organization_id": organization_id,
        "team_id": str(primary_team["team_id"]) if primary_team else None,
        "team_ids": team_ids
    }
