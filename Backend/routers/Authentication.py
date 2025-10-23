# import os
# import jwt
# import bcrypt
# from datetime import datetime, timedelta
# from fastapi import Depends, HTTPException, status, APIRouter
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from core.database import get_db
# from core.models import RegisterRequest, LoginRequest

# router = APIRouter(prefix="/api/auth", tags=["Auth"])

# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-this")
# JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

# security = HTTPBearer()
# #auth helper function
# def hash_password(password: str) -> str:
#     """Hash a password using bcrypt"""
#     return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password against a hash"""
#     return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# def create_access_token(data: dict) -> str:
#     """Create a JWT access token"""
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# def decode_token(token: str) -> dict:
#     """Decode and verify a JWT token"""
#     try:
#         payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
#         return payload
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.JWTError:
#         raise HTTPException(status_code=401, detail="Could not validate credentials")

# async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """Dependency to get current authenticated user"""
#     token = credentials.credentials
#     payload = decode_token(token)
#     user_id = payload.get("user_id")
#     if user_id is None:
#         raise HTTPException(status_code=401, detail="Could not validate credentials")
#     return user_id


# # authentication api endpoints
# @router.post("/register", status_code=status.HTTP_201_CREATED)
# def register(data: RegisterRequest):
#     """Register a new user"""
#     with get_db() as conn:
#         cursor = conn.cursor()

#         # Check if user already exists
#         cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
#         if cursor.fetchone():
#             raise HTTPException(status_code=400, detail="Email already registered")

#         # Check if password column exists, if not add it
#         cursor.execute("""
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_name='users' AND column_name='password_hash'
#         """)
#         if not cursor.fetchone():
#             cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
#             conn.commit()

#         # Hash password and create user
#         hashed_password = hash_password(data.password)
#         cursor.execute("""
#             INSERT INTO users (organization_id, first_name, second_name, role, email, password_hash)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             RETURNING id, organization_id, first_name, second_name, role, email, created_at
#         """, (data.organization_id, data.first_name, data.second_name, data.role, data.email, hashed_password))

#         user = cursor.fetchone()
#         conn.commit()

#         # Create JWT token
#         token = create_access_token({"user_id": user['id'], "email": user['email']})

#         return {
#             "success": True,
#             "token": token,
#             "user": dict(user)
#         }


# @router.post("/login")
# def login(data: LoginRequest):
#     """Login user and return JWT token"""
#     with get_db() as conn:
#         cursor = conn.cursor()

#         # Check if password column exists
#         cursor.execute("""
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_name='users' AND column_name='password_hash'
#         """)
#         password_column_exists = cursor.fetchone()

#         if not password_column_exists:
#             # For demo purposes, allow login without password (backward compatibility)
#             cursor.execute("""
#                 SELECT id, organization_id, first_name, second_name, role, email, created_at
#                 FROM users WHERE email = %s
#             """, (data.email,))
#             user = cursor.fetchone()

#             if not user:
#                 raise HTTPException(status_code=401, detail="Invalid email or password")

#             # Create JWT token
#             token = create_access_token({"user_id": user['id'], "email": user['email']})

#             return {
#                 "success": True,
#                 "token": token,
#                 "user": dict(user)
#             }

#         # Get user with password hash
#         cursor.execute("""
#             SELECT id, organization_id, first_name, second_name, role, email, password_hash, created_at
#             FROM users WHERE email = %s
#         """, (data.email,))

#         user = cursor.fetchone()

#         if not user:
#             raise HTTPException(status_code=401, detail="Invalid email or password")

#         # Verify password
#         if not verify_password(data.password, user['password_hash']):
#             raise HTTPException(status_code=401, detail="Invalid email or password")

#         # Remove password_hash from user dict
#         user_data = {k: v for k, v in user.items() if k != 'password_hash'}

#         # Create JWT token
#         token = create_access_token({"user_id": user['id'], "email": user['email']})

#         return {
#             "success": True,
#             "token": token,
#             "user": user_data
#         }


# @router.get("/me")
# async def get_current_user_info(user_id: int = Depends(get_current_user)):
#     """Get current authenticated user information"""
#     with get_db() as conn:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT id, organization_id, first_name, second_name, role, email, created_at
#             FROM users WHERE id = %s
#         """, (user_id,))
#         user = cursor.fetchone()

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         return {"success": True, "data": user}

import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Auth"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

# ------------------------------
# Auth Helper
# ------------------------------

def verify_supabase_token(token: str):
    """
    Verifies the Supabase access token and returns the associated user.
    """
    try:
        result = supabase.auth.get_user(token)
        user = result.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        print("❌ Token verification failed:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_supabase_token(token)
    return user

# ------------------------------
# Routes
# ------------------------------

@router.get("/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """
    Get the current Supabase-authenticated user info.
    """
    return {
        "success": True,
        "data": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
            "app_metadata": user.app_metadata,
            "user_metadata": user.user_metadata
        }
    }

@router.get("/protected")
async def protected_example(user = Depends(get_current_user)):
    """
    Example of a protected route — accessible only with a valid Supabase token.
    """
    return {
        "success": True,
        "message": f"Hello, {user.email}! You have accessed a protected route."
    }

