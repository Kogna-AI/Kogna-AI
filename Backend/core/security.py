from datetime import datetime, timedelta
import secrets
import hashlib

from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError

from core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


def create_access_token(data: dict) -> str:
    """Create a signed JWT access token.

    Security features:
    - Short expiration (15 minutes)
    - Includes iat (issued at) and exp (expiration) claims
    - Token type claim to distinguish from refresh tokens
    """
    to_encode = data.copy()

    now = datetime.utcnow()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "iat": int(now.timestamp()),
            "exp": expire,
            "token_type": "access",
        }
    )

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def create_refresh_token(data: dict) -> tuple[str, str, datetime]:
    """Create a signed JWT refresh token with a unique JTI.

    Returns:
        tuple: (token, jti, expires_at)
            - token: The signed JWT string
            - jti: Unique token identifier (to store in DB)
            - expires_at: When the token expires

    Security features:
    - Long expiration (30 days)
    - Unique JTI for revocation support
    - Token type claim for validation
    """
    to_encode = data.copy()

    now = datetime.utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Generate cryptographically secure random JTI
    jti = secrets.token_urlsafe(32)

    to_encode.update(
        {
            "iat": int(now.timestamp()),
            "exp": expire,
            "jti": jti,
            "token_type": "refresh",
        }
    )

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti, expire


def hash_token(token: str) -> str:
    """Create a SHA256 hash of a token for secure storage.

    We hash refresh tokens before storing them in the database so that
    even if the DB is compromised, the tokens cannot be used directly.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> dict:
    """Verify and decode an access token.

    Raises:
        HTTPException: 401 if token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Enforce token type to prevent refresh tokens being used as access tokens
        token_type = payload.get("token_type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def decode_refresh_token(token: str) -> dict:
    """Verify and decode a refresh token.

    Raises:
        HTTPException: 401 if token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Enforce token type
        token_type = payload.get("token_type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Ensure JTI is present
        if "jti" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
