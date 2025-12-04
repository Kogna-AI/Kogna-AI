from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor

from core.security import create_access_token
from core.database import get_db
from auth.dependencies import get_current_user


router = APIRouter(prefix="/api/auth", tags=["Auth"])

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)



# ------------------------------
# Request Models
# ------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    organization_id: str
    first_name: str
    second_name: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ------------------------------
# POST /register
# ------------------------------
@router.post("/register")
async def register(data: RegisterRequest, db=Depends(get_db)):
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = pwd_context.hash(data.password)

        cursor.execute("""
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
            RETURNING id, supabase_id
        """, (
            data.organization_id,
            data.first_name,
            data.second_name,
            data.role,
            data.email,
            hashed_password
        ))

        user = cursor.fetchone()
        conn.commit()

        return {
            "success": True,
            "user_id": user["id"],
            "supabase_id": user["supabase_id"]
        }



# ------------------------------
# POST /login
# ------------------------------
@router.post("/login")
async def login(data: LoginRequest, db=Depends(get_db)):
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id, email, password_hash, organization_id, supabase_id
            FROM users
            WHERE email = %s
        """, (data.email,))

        user = cursor.fetchone()

        if not user or not user["password_hash"]:
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        if not pwd_context.verify(data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        token_data = {
            "sub": user["supabase_id"],
            "email": user["email"],
            "organization_id": user["organization_id"]
        }

        access_token = create_access_token(token_data)

        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "organization_id": user["organization_id"]
            }
        }



# ------------------------------
# GET /me
# ------------------------------
@router.get("/me")
async def me(user = Depends(get_current_user)):
    """
    Show user info extracted from token.
    """
    return {
        "success": True,
        "data": user
    }
