import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv
import logging # Added logging
from core.database import get_db 
from psycopg2.extras import RealDictCursor 
from gotrue import User as SupabaseUser

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Auth"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(" Missing SUPABASE_URL or SUPABASE_KEY in environment variables")

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
            # Token was processed but returned no user, usually a deep-auth failure
            logging.warning("Supabase returned null user for token.")
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        # Changed print() to logging.error()
        logging.error("Token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = verify_supabase_token(token)
    return user

# ------------------------------
# NEW DEPENDENCY: Resolves UUID to Internal IDs
# ------------------------------

async def get_backend_user_id(
    supabase_user: SupabaseUser = Depends(get_current_user), 
    db = Depends(get_db)
) -> dict:
    """
    Verifies token, looks up the user's application row in the 'users' table 
    using the Supabase UUID, and returns the application IDs.
    """
    # The ID from the token (e.g., 9f8e1899-e1b5...)
    supabase_id = supabase_user.id 
    
    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # CRITICAL QUERY: Finds the user using the Supabase UUID 
        # and retrieves the internal Primary Key ('id') and 'organization_id'.
        cursor.execute(
            "SELECT id, organization_id FROM users WHERE supabase_id = %s", 
            (supabase_id,)
        )
        backend_user = cursor.fetchone()
        
        if not backend_user:
            # NOTE: If this 404 is hit, it means the token was valid, but the user is
            # not synced to your local PostgreSQL database yet.
            logging.warning("User profile (Supabase ID: %s) not found in backend database.", supabase_id)
            raise HTTPException(status_code=404, detail="User profile not found in backend database.")
            
        # Returns the IDs needed for RAG and scoping
        return {
            "user_id": str(backend_user['id']), 
            "organization_id": str(backend_user['organization_id'])
        }
    
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