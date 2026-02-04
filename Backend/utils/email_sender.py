"""
Email Sending Utility
Handles sending emails via SendGrid or SMTP.
This is a low-level utility - no business logic here.
"""

import os
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()

# Try to import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.warning("SendGrid not installed. Install with: pip install sendgrid")

# SMTP is always available (built-in)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Low-level email sending utility.
    Sends emails via SendGrid (preferred) or SMTP (fallback).
    """
    
    # Configuration from environment variables
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "verify@kogna.io")
    
    # SendGrid configuration
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    
    # SMTP configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using configured provider.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML version of email body
            text_content: Plain text fallback (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Validate inputs
        if not to_email or not subject or not html_content:
            logger.error("Missing required email parameters")
            return False
        
        try:
            # Try SendGrid first (if configured and available)
            if SENDGRID_AVAILABLE and EmailSender.SENDGRID_API_KEY:
                logger.info(f"Attempting to send email via SendGrid to {to_email}")
                return EmailSender._send_via_sendgrid(to_email, subject, html_content)
            
            # Fallback to SMTP
            elif EmailSender.SMTP_USERNAME and EmailSender.SMTP_PASSWORD:
                logger.info(f"Attempting to send email via SMTP to {to_email}")
                return EmailSender._send_via_smtp(to_email, subject, html_content, text_content)
            
            else:
                logger.error("No email provider configured! Set SENDGRID_API_KEY or SMTP credentials.")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False
    
    @staticmethod
    def _send_via_sendgrid(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email via SendGrid.
        
        Returns:
            True if successful
        """
        try:
            message = Mail(
                from_email=EmailSender.FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(EmailSender.SENDGRID_API_KEY)
            response = sg.send(message)
            
            # SendGrid returns 202 for accepted emails
            success = response.status_code in [200, 201, 202]
            
            if success:
                logger.info(f"✓ SendGrid email sent to {to_email}, status: {response.status_code}")
            else:
                logger.warning(f"✗ SendGrid returned status {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False
    
    @staticmethod
    def _send_via_smtp(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP (Gmail, Outlook, etc.).
        
        Returns:
            True if successful
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EmailSender.FROM_EMAIL
            msg['To'] = to_email
            
            # Add plain text version if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect and send
            with smtplib.SMTP(EmailSender.SMTP_SERVER, EmailSender.SMTP_PORT) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(EmailSender.SMTP_USERNAME, EmailSender.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✓ SMTP email sent to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected SMTP error: {e}")
            return False
    
    @staticmethod
    def get_verification_email_html(
        verification_url: str,
        first_name: Optional[str] = None
    ) -> str:
        """
        Generate HTML template for email verification.
        
        Args:
            verification_url: Full URL with token
            first_name: User's first name for personalization
            
        Returns:
            HTML string
        """
        name = first_name if first_name else "there"
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 32px;
            font-weight: 700;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .content h2 {{
            color: #1a1a1a;
            font-size: 24px;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .content p {{
            color: #555555;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .button-container {{
            text-align: center;
            margin: 35px 0;
        }}
        .verify-button {{
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s;
        }}
        .verify-button:hover {{
            transform: translateY(-2px);
        }}
        .alt-link {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            word-break: break-all;
        }}
        .alt-link p {{
            margin: 5px 0;
            font-size: 14px;
            color: #666666;
        }}
        .alt-link a {{
            color: #667eea;
            text-decoration: none;
            font-size: 12px;
        }}
        .warning-box {{
            background-color: #FEF3C7;
            border-left: 4px solid #F59E0B;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .warning-box strong {{
            color: #92400E;
        }}
        .warning-box p {{
            margin: 5px 0;
            color: #78350F;
            font-size: 14px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 5px 0;
            font-size: 13px;
            color: #6b7280;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🚀 Kogna.io</h1>
        </div>
        
        <div class="content">
            <h2>Welcome to Kogna, {name}! 🎉</h2>
            
            <p>Thank you for signing up! We're thrilled to have you on board.</p>
            
            <p>To get started and unlock all features, please verify your email address by clicking the button below:</p>
            
            <div class="button-container">
                <a href="{verification_url}" class="verify-button">
                    Verify Email Address
                </a>
            </div>
            
            <div class="alt-link">
                <p><strong>Button not working?</strong></p>
                <p>Copy and paste this link into your browser:</p>
                <a href="{verification_url}">{verification_url}</a>
            </div>
            
            <div class="warning-box">
                <strong>⏰ Important:</strong>
                <p>This verification link will expire in 24 hours for security reasons.</p>
            </div>
            
            <p style="margin-top: 30px;">If you have any questions, feel free to reach out to our support team.</p>
        </div>
        
        <div class="footer">
            <p><strong>Didn't create an account?</strong></p>
            <p>You can safely ignore this email. No account was created.</p>
            <p style="margin-top: 20px;">© 2024 Kogna.io. All rights reserved.</p>
            <p><a href="{EmailSender.FRONTEND_URL}">Visit our website</a></p>
        </div>
    </div>
</body>
</html>
        """.strip()
    
    @staticmethod
    def get_password_reset_email_html(
        reset_url: str,
        first_name: Optional[str] = None
    ) -> str:
        """
        Generate HTML template for password reset.
        
        Args:
            reset_url: Full URL with reset token
            first_name: User's first name for personalization
            
        Returns:
            HTML string
        """
        name = first_name if first_name else "there"
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            margin: 0;
            font-size: 32px;
            font-weight: 700;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .content h2 {{
            color: #1a1a1a;
            font-size: 24px;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .content p {{
            color: #555555;
            margin-bottom: 15px;
            font-size: 16px;
        }}
        .button-container {{
            text-align: center;
            margin: 35px 0;
        }}
        .reset-button {{
            display: inline-block;
            padding: 16px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s;
        }}
        .alt-link {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            word-break: break-all;
        }}
        .alt-link a {{
            color: #667eea;
            text-decoration: none;
            font-size: 12px;
        }}
        .warning-box {{
            background-color: #FEE2E2;
            border-left: 4px solid #EF4444;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            font-size: 13px;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🔐 Kogna.io</h1>
        </div>
        
        <div class="content">
            <h2>Password Reset Request</h2>
            
            <p>Hi {name},</p>
            
            <p>We received a request to reset the password for your Kogna.io account. No problem, it happens!</p>
            
            <p>Click the button below to set up a new password:</p>
            
            <div class="button-container">
                <a href="{reset_url}" class="reset-button">
                    Reset My Password
                </a>
            </div>
            
            <div class="alt-link">
                <p><strong>Link not working?</strong> Copy and paste this:</p>
                <a href="{reset_url}">{reset_url}</a>
            </div>
            
            <div class="warning-box">
                <p style="color: #991B1B; margin: 0;"><strong>⏰ Security Note:</strong> This link will expire in <strong>1 hour</strong> for your protection.</p>
            </div>
            
            <p>If you didn't request this, you can safely ignore this email. Your password will remain unchanged.</p>
        </div>
        
        <div class="footer">
            <p>© 2024 Kogna.io. All rights reserved.</p>
            <p><a href="{EmailSender.FRONTEND_URL}">Visit our website</a></p>
        </div>
    </div>
</body>
</html>
        """.strip()

    @staticmethod
    def test_configuration() -> dict:
        """
        Test email configuration and return status.
        
        Returns:
            Dict with configuration status
        """
        status = {
            "sendgrid_configured": bool(EmailSender.SENDGRID_API_KEY),
            "sendgrid_available": SENDGRID_AVAILABLE,
            "smtp_configured": bool(EmailSender.SMTP_USERNAME and EmailSender.SMTP_PASSWORD),
            "can_send_emails": False,
            "provider": None
        }
        
        if SENDGRID_AVAILABLE and EmailSender.SENDGRID_API_KEY:
            status["can_send_emails"] = True
            status["provider"] = "SendGrid"
        elif EmailSender.SMTP_USERNAME and EmailSender.SMTP_PASSWORD:
            status["can_send_emails"] = True
            status["provider"] = "SMTP"
        
        return status