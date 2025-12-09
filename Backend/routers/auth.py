from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor

from core.security import create_access_token
from core.database import get_db
from auth.dependencies import get_current_user
from core.models import RegisterRequest, LoginRequest
from argon2 import PasswordHasher
ph = PasswordHasher()


router = APIRouter(prefix="/api/auth", tags=["Auth"])

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


# ------------------------------
# POST /register
# ------------------------------
from argon2 import PasswordHasher

ph = PasswordHasher()

@router.post("/register")
async def register(data: RegisterRequest, db=Depends(get_db)):
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # 1. Email uniqueness check
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (data.email,)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )

            # 2. Find or create organization
            cursor.execute(
                "SELECT id FROM organizations WHERE name = %s",
                (data.organization,)
            )
            org = cursor.fetchone()

            if not org:
                cursor.execute(
                    """
                    INSERT INTO organizations (id, name)
                    VALUES (gen_random_uuid(), %s)
                    RETURNING id
                    """,
                    (data.organization,)
                )
                org = cursor.fetchone()

            organization_id = org["id"]

            # 3. Hash password using Argon2
            hashed_password = ph.hash(data.password)

            # 4. Create user (auth user)
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
                organization_id,
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
                "supabase_id": user["supabase_id"],
                "organization_id": organization_id
            }

        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to register: {str(e)}"
            )



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
