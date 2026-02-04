"""
Password Reset Service
Business logic for password recovery.
Part of authentication system.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from core.database import get_db_context
from utils.email_sender import EmailSender
import logging

logger = logging.getLogger(__name__)


class PasswordReset:
    """
    Handles password reset business logic.
    Follows the same security patterns as EmailVerification.
    """
    
    # Configuration
    TOKEN_EXPIRY_HOURS = 1  # Password resets usually expire faster for security
    TOKEN_LENGTH = 32
    
    @staticmethod
    def request_reset(email: str) -> Tuple[bool, str]:
        """
        Initiate password reset process for a given email.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Password reset requested for {email}")
            
            with get_db_context() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, first_name, email 
                    FROM users 
                    WHERE email = %s
                """, (email,))
                
                user = cursor.fetchone()
                
                # Security Best Practice: Don't reveal if email exists
                if not user:
                    logger.info(f"Reset failed: Email {email} not found (silent fail)")
                    return True, "If that email is registered, a reset link has been sent."

                user_id = str(user['id'])
                
                # Step 1: Generate reset token
                token = PasswordReset._generate_token(user_id)
                
                # Step 2: Build reset URL
                # Matches your frontend pattern: /reset-password?token=...
                reset_url = f"{EmailSender.FRONTEND_URL}/reset-password?token={token}"
                
                # Step 3: Get HTML template (Assumes EmailSender has this method)
                html_content = EmailSender.get_password_reset_email_html(
                    reset_url=reset_url,
                    first_name=user.get('first_name')
                )
                
                # Step 4: Send email
                email_sent = EmailSender.send_email(
                    to_email=email,
                    subject="Reset your Kogna.io password 🔐",
                    html_content=html_content
                )
                
                if email_sent:
                    return True, "Password reset link sent to your inbox."
                else:
                    return False, "Failed to send reset email. Please try again later."

        except Exception as e:
            logger.error(f"Error in request_reset: {e}", exc_info=True)
            return False, f"Error: {str(e)}"

    @staticmethod
    def _generate_token(user_id: str) -> str:
        """
        Generate and store reset token. Consistent with EmailVerification._generate_token.
        """
        token = secrets.token_urlsafe(PasswordReset.TOKEN_LENGTH)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=PasswordReset.TOKEN_EXPIRY_HOURS
        )
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Invalidate any old password reset tokens
            cursor.execute("""
                DELETE FROM verification_tokens 
                WHERE user_id = %s 
                AND token_type = 'password_reset'
                AND used_at IS NULL
            """, (user_id,))
            
            # Insert new reset token
            cursor.execute("""
                INSERT INTO verification_tokens 
                (user_id, token, token_type, expires_at, created_at, updated_at)
                VALUES (%s, %s, 'password_reset', %s, %s, %s)
            """, (
                user_id,
                token,
                expires_at,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            
            conn.commit()
        
        return token

    @staticmethod
    def verify_reset_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify if a reset token is valid without using it yet.
        Used by frontend to show the 'New Password' form.
        """
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, expires_at, used_at
                FROM verification_tokens
                WHERE token = %s AND token_type = 'password_reset'
            """, (token,))
            
            result = cursor.fetchone()
            
            if not result:
                return False, None, "Invalid reset link."
            
            if result['used_at']:
                return False, None, "This link has already been used."
                
            if datetime.now(timezone.utc) > result['expires_at']:
                return False, None, "This link has expired."
                
            return True, str(result['user_id']), None

    @staticmethod
    def complete_reset(token: str, new_password_hash: str) -> Tuple[bool, str]:
        """
        Actually update the password and mark token as used.
        """
        # 1. Verify token first
        is_valid, user_id, error = PasswordReset.verify_reset_token(token)
        if not is_valid:
            return False, error or "Invalid token"

        try:
            with get_db_context() as conn:
                cursor = conn.cursor()
                current_time = datetime.now(timezone.utc)
                
                # 2. Update the user's password
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s, 
                        updated_at = %s
                    WHERE id = %s
                """, (new_password_hash, current_time, user_id))
                
                # 3. Mark token as used
                cursor.execute("""
                    UPDATE verification_tokens
                    SET used_at = %s, updated_at = %s
                    WHERE token = %s AND token_type = 'password_reset'
                """, (current_time, current_time, token))
                
                conn.commit()
                logger.info(f"✓ Password successfully reset for user {user_id}")
                return True, "Your password has been reset successfully."
                
        except Exception as e:
            logger.error(f"Failed to complete password reset: {e}")
            return False, "An error occurred while updating your password."