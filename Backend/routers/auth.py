from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor
import logging
from auth.email_verification import EmailVerification
import uuid
import bcrypt
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
)
from core.database import get_db
from core.permissions import UserContext, get_user_context
from core.models import RegisterRequest, LoginRequest
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

router = APIRouter(prefix="/api/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

ph = PasswordHasher()

# Cookie configuration for refresh tokens
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days in seconds


def _validate_password_strength(password: str) -> None:
    """Server-side password policy enforcement.

    Applied ONLY to new registrations to avoid breaking existing passwords.
    Requirements:
    - At least 8 characters
    - Contains at least one letter and one digit
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )

    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_letter and has_digit):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one letter and one digit",
        )


# ------------------------------
# POST /register
# ------------------------------

@router.post("/register")
async def register(data: RegisterRequest, db=Depends(get_db)):
    # Enforce password policy for new accounts only
    _validate_password_strength(data.password)

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
            user_id = user["id"]

            # 5. Auto-create default team for new organization
            # Check if this is the first user in the organization
            cursor.execute(
                "SELECT COUNT(*) AS count FROM users WHERE organization_id = %s",
                (organization_id,)
            )
            user_count = cursor.fetchone()["count"]

            if user_count == 1:  # First user in the organization
                # Create a default team
                cursor.execute(
                    """
                    INSERT INTO teams (id, organization_id, name)
                    VALUES (gen_random_uuid(), %s, %s)
                    RETURNING id
                    """,
                    (organization_id, "Operations")
                )
                team = cursor.fetchone()
                team_id = team["id"]

                # Add user as a member of the team
                cursor.execute(
                    """
                    INSERT INTO team_members (
                        id,
                        team_id,
                        user_id,
                        role,
                        performance,
                        capacity,
                        project_count,
                        status
                    )
                    VALUES (gen_random_uuid(), %s, %s, %s, 85, 80, 0, 'available')
                    """,
                    (team_id, user_id, data.role)
                )

                # Assign highest RBAC role (founder/executive) to the first user
                cursor.execute(
                    """
                    SELECT id
                    FROM roles
                    ORDER BY level DESC
                    LIMIT 1
                    """,
                )
                highest_role = cursor.fetchone()
                if highest_role:
                    cursor.execute(
                        """
                        INSERT INTO user_roles (user_id, role_id)
                        VALUES (%s, %s)
                        """,
                        (user_id, highest_role["id"]),
                    )

            conn.commit()

            success, message = EmailVerification.generate_and_send_verification(
                user_id=str(user_id),
                email=data.email,
                first_name=data.first_name
            )
            
            if not success:
                logger.warning(f"Failed to send verification email: {message}")
                # Don't fail registration if email fails, just log it

            return {
                "success": True,
                "message": "Registration successful! Please check your email to verify your account.",
                "user_id": user["id"],
                "supabase_id": user["supabase_id"],
                "organization_id": organization_id,
                "email_sent": success
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
async def login(
    data: LoginRequest,
    response: Response,
    request: Request,
    db=Depends(get_db),
):
    email = data.email.strip().lower()

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT id, email, password_hash, organization_id, supabase_id, email_verified
            FROM users
            WHERE LOWER(email) = %s
            """,
            (email,),
        )

        user = cursor.fetchone()

        invalid_credentials_exc = HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

        if not user or not user["password_hash"]:
            try:
                ph.verify(ph.hash("dummy-password"), data.password)
            except Exception:
                pass
            raise invalid_credentials_exc

        # Password verification
        try:
            ph.verify(user["password_hash"], data.password)
        except VerifyMismatchError:
            raise invalid_credentials_exc

        #  ADD THIS: Check email verification
        if not user.get("email_verified", False):
            raise HTTPException(
                status_code=403,
                detail="Please verify your email before logging in. Check your inbox for the verification link."
            )

        # --- Create tokens ---
        token_data = {
            "sub": str(user["id"]),  # Use actual user ID, not supabase_id
            "email": user["email"],
            "organization_id": str(user["organization_id"]),
        }

        access_token = create_access_token(token_data)
        refresh_token, jti, expires_at = create_refresh_token(token_data)

        # Store refresh token in database for revocation support
        token_hash = hash_token(refresh_token)
        user_agent = request.headers.get("user-agent", "")
        # Note: request.client.host might be proxy IP; consider X-Forwarded-For
        ip_address = request.client.host if request.client else None

        cursor.execute(
            """
            INSERT INTO refresh_tokens (jti, user_id, token_hash, expires_at, user_agent, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (jti, user["id"], token_hash, expires_at, user_agent, ip_address),
        )
        conn.commit()

        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=refresh_token,
            max_age=REFRESH_TOKEN_COOKIE_MAX_AGE,
            httponly=True,  # Cannot be accessed by JavaScript
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",  # Lax is fine for localhost:3000 -> localhost:8000 (same-site)
            path="/",  # Root path so /api/auth/refresh will see the cookie
        )

        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "organization_id": user["organization_id"],
            },
        }




# ------------------------------
# POST /refresh
# ------------------------------
@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db=Depends(get_db),
):
    """Issue a new access token using the refresh token from httpOnly cookie.

    Security features:
    - Validates refresh token signature and expiration
    - Checks token hasn't been revoked in database
    - Issues new short-lived access token
    - Does NOT rotate refresh token (you can add rotation for extra security)
    """
    # Read refresh token from httpOnly cookie
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token provided",
        )

    # Decode and validate refresh token
    try:
        payload = decode_refresh_token(refresh_token)
    except HTTPException:
        # Token is invalid or expired; clear the cookie
        response.delete_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            path="/",
        )
        raise

    jti = payload["jti"]
    token_hash = hash_token(refresh_token)

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Verify token exists in DB and hasn't been revoked
        cursor.execute(
            """
            SELECT user_id, revoked_at, expires_at
            FROM refresh_tokens
            WHERE jti = %s AND token_hash = %s
            """,
            (jti, token_hash),
        )

        token_record = cursor.fetchone()

        if not token_record:
            # Token not found in DB (possibly never issued or already deleted)
            response.delete_cookie(
                key=REFRESH_TOKEN_COOKIE_NAME,
                path="/",
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        if token_record["revoked_at"] is not None:
            # Token has been revoked (logout or security event)
            response.delete_cookie(
                key=REFRESH_TOKEN_COOKIE_NAME,
                path="/",
            )
            raise HTTPException(
                status_code=401,
                detail="Refresh token has been revoked",
            )

        # Token is valid; issue new access token
        token_data = {
            "sub": payload["sub"],
            "email": payload["email"],
            "organization_id": payload["organization_id"],
        }

        access_token = create_access_token(token_data)

        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
        }


# ------------------------------
# POST /logout
# ------------------------------
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db=Depends(get_db),
):
    """Logout by revoking the refresh token and clearing the cookie.

    Security features:
    - Marks refresh token as revoked in database
    - Clears httpOnly cookie
    - Prevents reuse of the refresh token
    """
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)
            jti = payload["jti"]
            token_hash = hash_token(refresh_token)

            with db as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                # Mark token as revoked
                cursor.execute(
                    """
                    UPDATE refresh_tokens
                    SET revoked_at = NOW()
                    WHERE jti = %s AND token_hash = %s
                    """,
                    (jti, token_hash),
                )
                conn.commit()

        except HTTPException:
            # Token is already invalid; just clear cookie
            pass

    # Clear refresh token cookie regardless of DB operation result
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path="/",
    )

    return {
        "success": True,
        "message": "Logged out successfully",
    }

@router.get("/verify-email")
async def verify_email(token: str):
    """
    Verify user's email address using the token from the email link.
    
    Query parameter:
        token: Verification token from email
    """
    success, user_id, error_message = EmailVerification.verify_token(token)
    
    if success:
        return {
            "success": True,
            "message": "Email verified successfully! You can now log in.",
            "user_id": user_id
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=error_message or "Verification failed"
        )
    
@router.post("/resend-verification")
async def resend_verification_email(request: Request):
    """
    Resend verification email to a user.
    
    Body:
        email: User's email address
    """
    body = await request.json()
    email = body.get("email", "").strip().lower()
    
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )
    
    success, message = EmailVerification.resend_verification(email)
    
    if success:
        return {
            "success": True,
            "message": message
        }
    else:
        # Return 200 even for errors to avoid email enumeration
        # But you can return 400 if the email is already verified
        return {
            "success": False,
            "message": message
        }
       
# ------------------------------
# GET /me
# ------------------------------
@router.get("/me")
async def me(
    user_ctx: UserContext = Depends(get_user_context),
    db=Depends(get_db),
):
    user_id = user_ctx.id

    with db as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                u.id,
                u.organization_id,
                u.first_name,
                u.second_name,
                u.role,
                u.email,
                u.email_verified,
                u.email_verified_at,
                u.created_at,
                o.name as organization_name
            FROM users u
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE u.id = %s
            """,
            (user_id,),
        )

        user_data = cursor.fetchone()

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        data = dict(user_data)
        data["rbac"] = {
            "role_name": user_ctx.role_name,
            "role_level": user_ctx.role_level,
            "permissions": user_ctx.permissions,
            "team_ids": user_ctx.team_ids,
        }

        return {
            "success": True,
            "data": data,
        }