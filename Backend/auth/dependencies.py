from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 
from psycopg2.extras import RealDictCursor

from core.security import decode_access_token
from core.database import get_db

bearer_scheme = HTTPBearer(auto_error=True)



from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=True)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    # dev shortcut
    if token == "system-admin-dev":
        return {
            "supabase_id": "system",
            "email": "system@kogna.ai",
            "organization_id": "kogna_internal",
            "is_system_admin": True,
        }

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "supabase_id": payload["sub"],
        "email": payload.get("email"),
        "organization_id": payload.get("organization_id"),
        "is_system_admin": False,
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
