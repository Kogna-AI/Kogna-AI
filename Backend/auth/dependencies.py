from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from psycopg2.extras import RealDictCursor

from core.security import decode_access_token
from core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Reads the JWT and returns basic user identity.
    """
    payload = decode_access_token(token)
    return {
        "supabase_id": payload["sub"],
        "email": payload.get("email"),
    }


async def get_backend_user_id(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Uses the ID from JWT to look up user entry in database.
    """
    supabase_id = user["supabase_id"]

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id, organization_id FROM users WHERE supabase_id = %s",
            (supabase_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found in backend DB")

        return {
            "user_id": str(row["id"]),
            "organization_id": str(row["organization_id"]),
        }
