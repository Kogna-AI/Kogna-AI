"""
Email Verification Service
Business logic for email verification.
Part of authentication system.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from core.database import get_db_context
from utils.email_sender import EmailSender
import logging

logger = logging.getLogger(__name__)


class EmailVerification:
    """
    Handles email verification business logic.
    This is a security feature - always free, no subscription limits.
    """
    
    # Configuration
    TOKEN_EXPIRY_HOURS = 24
    TOKEN_LENGTH = 32  # URL-safe characters
    
    @staticmethod
    def generate_and_send_verification(
        user_id: str,
        email: str,
        first_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Generate verification token and send email.
        
        Args:
            user_id: User's UUID
            email: User's email address
            first_name: User's first name for personalization
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Step 1: Generate token
            token = EmailVerification._generate_token(user_id)
            logger.info(f"Generated verification token for user {user_id}")
            
            # Step 2: Build verification URL
            verification_url = f"{EmailSender.FRONTEND_URL}/verify-email?token={token}"
            logger.info(f"Verification URL: {verification_url}")
            
            # Step 3: Get HTML email template
            html_content = EmailSender.get_verification_email_html(
                verification_url=verification_url,
                first_name=first_name
            )
            
            # Step 4: Send email
            email_sent = EmailSender.send_email(
                to_email=email,
                subject="Verify your Kogna.io account 🚀",
                html_content=html_content
            )
            
            if email_sent:
                logger.info(f"✓ Verification email sent to {email}")
                return True, "Verification email sent successfully"
            else:
                logger.warning(f"✗ Failed to send verification email to {email}")
                return False, "Failed to send verification email. Please try again."
            
        except Exception as e:
            logger.error(f"Error in generate_and_send_verification: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def _generate_token(user_id: str) -> str:
        """
        Generate and store verification token in database.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Token string
        """
        # Generate cryptographically secure random token
        token = secrets.token_urlsafe(EmailVerification.TOKEN_LENGTH)
        
        # Calculate expiry time
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=EmailVerification.TOKEN_EXPIRY_HOURS
        )
        
        # Store in database
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Delete any existing unused verification tokens for this user
            # (User can only have one active verification token at a time)
            cursor.execute("""
                DELETE FROM verification_tokens 
                WHERE user_id = %s 
                AND token_type = 'email_verification'
                AND used_at IS NULL
            """, (user_id,))
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old verification token(s) for user {user_id}")
            
            # Insert new token
            cursor.execute("""
                INSERT INTO verification_tokens 
                (user_id, token, token_type, expires_at, created_at, updated_at)
                VALUES (%s, %s, 'email_verification', %s, %s, %s)
            """, (
                user_id,
                token,
                expires_at,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            
            conn.commit()
            logger.info(f"Stored verification token in database (expires: {expires_at})")
        
        return token
    
    @staticmethod
    def verify_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify email verification token and mark user as verified.
        
        Args:
            token: Verification token from email link
            
        Returns:
            Tuple of (success, user_id, error_message)
            - success: True if verification succeeded
            - user_id: User's ID if successful, None otherwise
            - error_message: Error description if failed, None if successful
        """
        logger.info(f"Attempting to verify token: {token[:10]}...")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Find token in database
            cursor.execute("""
                SELECT user_id, expires_at, used_at, created_at
                FROM verification_tokens
                WHERE token = %s 
                AND token_type = 'email_verification'
            """, (token,))
            
            result = cursor.fetchone()
            
            # Token not found
            if not result:
                logger.warning(f"Invalid token: not found in database")
                return False, None, "Invalid verification link. Please request a new one."
            
            user_id = str(result['user_id'])
            expires_at = result['expires_at']
            used_at = result['used_at']
            created_at = result['created_at']
            
            logger.info(f"Token found for user {user_id}, created {created_at}")
            
            # Check if token was already used
            if used_at:
                logger.warning(f"Token already used at {used_at}")
                return False, None, "This verification link has already been used. You can log in now."
            
            # Check if token has expired
            current_time = datetime.now(timezone.utc)
            if current_time > expires_at:
                logger.warning(f"Token expired at {expires_at}, current time {current_time}")
                return False, None, "This verification link has expired. Please request a new one."
            
            # Token is valid! Mark as used
            cursor.execute("""
                UPDATE verification_tokens
                SET used_at = %s, updated_at = %s
                WHERE token = %s
            """, (current_time, current_time, token))
            
            # Mark user as verified
            cursor.execute("""
                UPDATE users
                SET email_verified = TRUE,
                    email_verified_at = %s
                WHERE id = %s
            """, (current_time, user_id))
            
            # Check if update succeeded
            if cursor.rowcount == 0:
                logger.error(f"Failed to update user {user_id} - user not found")
                conn.rollback()
                return False, None, "User not found. Please contact support."
            
            conn.commit()
            
            logger.info(f"✓ Email verified successfully for user {user_id}")
            return True, user_id, None
    
    @staticmethod
    def is_verified(user_id: str) -> bool:
        """
        Check if user's email is verified.
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if email is verified, False otherwise
        """
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email_verified 
                FROM users 
                WHERE id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"User {user_id} not found when checking verification status")
                return False
            
            is_verified = result['email_verified'] or False
            logger.debug(f"User {user_id} verification status: {is_verified}")
            
            return is_verified
    
    @staticmethod
    def resend_verification(email: str) -> Tuple[bool, str]:
        """
        Resend verification email to a user.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Resend verification requested for {email}")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email_verified, first_name, email
                FROM users 
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            # Don't reveal if email exists (security best practice)
            if not user:
                logger.info(f"Email {email} not found (not revealing to user)")
                return True, "If that email is registered, a verification link has been sent."
            
            # Check if already verified
            if user['email_verified']:
                logger.info(f"Email {email} already verified")
                return False, "This email address is already verified. You can log in now."
        
        # Send new verification email
        success, message = EmailVerification.generate_and_send_verification(
            user_id=str(user['id']),
            email=user['email'],
            first_name=user.get('first_name')
        )
        
        if success:
            return True, "Verification email sent. Please check your inbox."
        else:
            logger.error(f"Failed to resend verification to {email}: {message}")
            return False, "Failed to send email. Please try again later."
    
    @staticmethod
    def get_user_verification_status(user_id: str) -> dict:
        """
        Get detailed verification status for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict with verification details
        """
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get user info
            cursor.execute("""
                SELECT email, email_verified, email_verified_at
                FROM users
                WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            
            if not user:
                return {
                    "user_found": False,
                    "email_verified": False
                }
            
            # Get pending token info
            cursor.execute("""
                SELECT created_at, expires_at
                FROM verification_tokens
                WHERE user_id = %s
                AND token_type = 'email_verification'
                AND used_at IS NULL
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            
            pending_token = cursor.fetchone()
            
            return {
                "user_found": True,
                "email": user['email'],
                "email_verified": user['email_verified'] or False,
                "verified_at": user['email_verified_at'].isoformat() if user['email_verified_at'] else None,
                "has_pending_token": pending_token is not None,
                "pending_token_expires_at": pending_token['expires_at'].isoformat() if pending_token else None
            }