"""
Email Verification API Endpoints
Handles verification, resending, and status checking.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, validator
from auth.email_verification import EmailVerification
from auth.dependencies import get_current_user
import logging

router = APIRouter(prefix="/api/auth", tags=["Email Verification"])
logger = logging.getLogger(__name__)


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class VerifyEmailRequest(BaseModel):
    """Request to verify email with token."""
    token: str
    
    @validator('token')
    def token_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Token cannot be empty')
        return v.strip()


class VerifyEmailResponse(BaseModel):
    """Response after email verification."""
    message: str
    verified: bool
    user_id: Optional[str] = None


class ResendVerificationRequest(BaseModel):
    """Request to resend verification email."""
    email: EmailStr


class ResendVerificationResponse(BaseModel):
    """Response after resending verification."""
    message: str
    email_sent: bool


class VerificationStatusResponse(BaseModel):
    """Response with verification status."""
    email_verified: bool
    user_id: str
    email: str
    verified_at: Optional[str] = None


# ============================================
# ENDPOINTS
# ============================================

@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify email address",
    description="Verify user's email address using the token sent via email"
)
async def verify_email(data: VerifyEmailRequest):
    """
    Verify email address with token.
    
    - **token**: Verification token from email link
    
    Returns verification result.
    """
    logger.info(f"Email verification request received")
    
    # Verify the token
    success, user_id, error = EmailVerification.verify_token(data.token)
    
    if not success:
        logger.warning(f"Email verification failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Email verification failed"
        )
    
    logger.info(f"✓ Email verified successfully for user {user_id}")
    
    return VerifyEmailResponse(
        message="Email verified successfully! You can now log in.",
        verified=True,
        user_id=user_id
    )


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    summary="Resend verification email",
    description="Resend verification email to a registered email address"
)
async def resend_verification(data: ResendVerificationRequest):
    """
    Resend verification email.
    
    - **email**: Email address to resend verification to
    
    Note: For security, this endpoint always returns success even if email doesn't exist.
    """
    logger.info(f"Resend verification requested for {data.email}")
    
    success, message = EmailVerification.resend_verification(data.email)
    
    # Always return 200 OK (don't reveal if email exists)
    return ResendVerificationResponse(
        message=message,
        email_sent=success
    )


@router.get(
    "/verification-status",
    response_model=VerificationStatusResponse,
    summary="Get verification status",
    description="Check if current user's email is verified (requires authentication)"
)
async def get_verification_status(user = Depends(get_current_user)):
    """
    Get verification status for authenticated user.
    
    Requires: Valid JWT token in Authorization header
    
    Returns current verification status.
    """
    logger.info(f"Verification status check for user {user['id']}")
    
    status_info = EmailVerification.get_user_verification_status(user['id'])
    
    if not status_info['user_found']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return VerificationStatusResponse(
        email_verified=status_info['email_verified'],
        user_id=user['id'],
        email=status_info['email'],
        verified_at=status_info.get('verified_at')
    )


# ============================================
# ADMIN/DEBUG ENDPOINTS (Optional)
# ============================================

@router.get(
    "/email-config-status",
    summary="Check email configuration",
    description="Debug endpoint to check email provider configuration"
)
async def get_email_config_status():
    """
    Check email service configuration.
    
    For debugging - shows which email provider is configured.
    Remove this endpoint in production for security.
    """
    from utils.email_sender import EmailSender
    
    config_status = EmailSender.test_configuration()
    
    return {
        "status": "configured" if config_status['can_send_emails'] else "not_configured",
        "provider": config_status['provider'],
        "details": config_status
    }