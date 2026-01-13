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
    Returns user_id and organization_id from JWT payload.
    No DB lookup needed since we store the user ID directly in JWT.
    """
    return {
        "user_id": str(user["id"]),
        "organization_id": str(user["organization_id"]),
    }
