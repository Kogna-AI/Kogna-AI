import os
import logging
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, ReplyTo

import ssl


# This overrides the global SSL context for the entire application
# Use this ONLY for local development to bypass the Mac/venv certificate issue
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

logger = logging.getLogger(__name__)

class WaitlistService:
    GOOGLE_SHEET_WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "verify@kogna.io")
    REPLY_TO_EMAIL = "GetKogna@outlook.com"

    @staticmethod
    def process_signup(data: dict) -> bool:
        # 1. Google Sheets Sync
        if WaitlistService.GOOGLE_SHEET_WEBHOOK_URL:
            try:
                requests.post(WaitlistService.GOOGLE_SHEET_WEBHOOK_URL, json=data, timeout=10)
            except Exception as e:
                logger.error(f"Google Sheet Error: {e}")

        # 2. SendGrid Email Trigger
        return WaitlistService.send_sendgrid_email(data.get("name"), data.get("email"))

    @staticmethod
    def send_sendgrid_email(name: str, email: str) -> bool:
        if not WaitlistService.SENDGRID_API_KEY:
            logger.error("SENDGRID_API_KEY is missing")
            return False

        html_content = f"""
        <html>
        <body style="margin: 0; padding: 20px 0; background-color: #f8fafc; font-family: Helvetica, Arial, sans-serif;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                    <td align="center">
                        <div style="max-width: 600px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden;">
                            
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-bottom: 1px solid #e2e8f0; padding: 20px 32px;">
                                <tr>
                                    <td align="left" style="vertical-align: middle;">
                                        <img src="https://kogna.io/KognaKLetterLogo.png" alt="Kogna" width="28" height="28" style="display: inline-block; vertical-align: middle;">
                                        <span style="margin-left: 8px; font-size: 20px; font-weight: 700; color: #020617; vertical-align: middle;">Kogna</span>
                                    </td>
                                    <td align="right" style="vertical-align: middle;">
                                        <a href="https://www.linkedin.com/company/kognaai">
                                            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="20" height="20" style="display: block;">
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <div style="padding: 40px 48px; text-align: left;">
                                <p style="font-size: 16px; line-height: 1.6; color: #475569; margin-bottom: 24px;">
                                    Welcome to <strong>Kogna</strong>, your <strong>Smart Radar for Business</strong>.
                                </p>
                                <p style="font-size: 16px; line-height: 1.6; color: #475569; margin-bottom: 24px;">
                                    Our mission is to help executives turn data chaos into strategic clarity. We are building a platform that provides unified visibility and real-time positioning insights to power high-impact decisions.
                                </p>
                                <p style="font-size: 16px; line-height: 1.6; color: #475569; margin-bottom: 32px;">
                                    We're currently pre-launch, so thank you for joining us early. We're excited to show you the future of human-centered AI.
                                </p>

                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-top: 32px;">
                                    <tr>
                                        <td align="left" style="font-size: 16px; color: #64748b; vertical-align: middle;">
                                        Want a deeper look?
                                        </td>
                                        <td align="right" style="vertical-align: middle;">
                                        <a href="https://calendly.com/getkogna/30min" style="color: #2563eb; font-size: 16px; font-weight: 600; text-decoration: none;">                                   
                                            Book a Call &rarr;
                                        </a>
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <div style="padding: 24px 48px; text-align: center; border-top: 1px solid #f1f5f9; background-color: #fcfdfe;">
                                <p style="font-size: 13px; color: #94a3b8; margin: 4px 0;">GetKogna@outlook.com  |  +1 (352) 727-5984</p>
                                <p style="font-size: 13px; color: #94a3b8; margin: 4px 0;">&copy; 2026 Kogna AI. All rights reserved.</p>
                            </div>
                        </div>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        message = Mail(
            from_email=WaitlistService.FROM_EMAIL,
            to_emails=email,
            subject='Welcome to Kogna',
            html_content=html_content
        )
        
        # Set reply-to so you get the responses at Outlook
        message.reply_to = ReplyTo(WaitlistService.REPLY_TO_EMAIL)

        try:
            sg = SendGridAPIClient(WaitlistService.SENDGRID_API_KEY)
            response = sg.send(message)
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"SendGrid Error: {e}")
            return False