import os
import re
import secrets
import smtplib
from dotenv import load_dotenv
import logging
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl

load_dotenv()

# Configure logging
log = logging.getLogger(__name__)
# Set log level from environment variable or default to WARNING
log_level = os.getenv('LOGGING', 'WARNING').upper()
if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    log_level = 'WARNING'
log.setLevel(getattr(logging, log_level, logging.WARNING))

# Email configuration
class Config:
    # Email server configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))  # Default to port 465 with SSL
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'true').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@familytree.com')
    MAIL_TIMEOUT = 30  # 30 seconds timeout
    MAIL_DEBUG = True  # Enable debug output
    MAIL_ASCII_ATTACHMENTS = False  # Handle non-ASCII attachments properly
    MAIL_SUPPRESS_SEND = False  # Actually send emails
    
    # Application configuration
    APP_NAME = os.getenv('APP_NAME', 'FamilyTreesPE')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5566')

class EmailPublisher:
    """
    Email Publisher class to handle the creation and 
    sending of email messages with support for both 
    plain text and HTML formats.
    """
    def __init__(self, email_sender: str, email_password: str):
        """
        Initialize the EmailPublisher with the sender's email and password.
        
        Args:
            email_sender (str): The sender's email address.
            email_password (str): The sender's email password.
        """
        self.email_sender = email_sender
        self.email_password = email_password
        
    def _create_email(self, subject: str, text: str, html: str, recipients: List[str]) -> MIMEMultipart:
        """
        Create an email message with both plain text 
        and HTML formats
        
        Args:
            subject (str): The subject of the email.
            text (str): The plain text content of the email.
            html (str): The HTML content of the email.
            recipients (List[str]): List of recipient email addresses.
            
        Returns:
            MIMEMultipart: The created email message object.
        """
        msg = MIMEMultipart("alternative")
        msg['From'] = self.email_sender
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        # Add both plain text and HTML parts
        if text:
            msg.attach(MIMEText(text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))
        
        return msg

    def publish_email(self, subject: str, text: str, html: str, recipients: List[str]):
        """
        Send email to multiple recipients
        
        Args:
            subject (str): The subject of the email.
            text (str): The plain text content of the email.
            html (str): The HTML content of the email.
            recipients (List[str]): List of recipient email addresses.
            
        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        try:
            # Create email message object
            msg = self._create_email(subject, text, html, recipients)
            
            # Create secure SSL connection
            context = ssl.create_default_context()
            context.load_default_certs()
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            # Send email
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT, context=context) as smtp:
                try:
                    smtp.login(self.email_sender, self.email_password)
                    smtp.sendmail(self.email_sender, recipients, msg.as_string())
                    return True
                except smtplib.SMTPAuthenticationError as e:
                    log.error(f'publish_email(): Login failed: {str(e)}')
                    return False
                except Exception as e:
                    log.error(f'publish_email(): Error sending email: {str(e)}')
                    return False
        except Exception as e:
            log.error(f'publish_email(): General error: {str(e)}')
            return False

def validate_email(email):
    """
    Check if email is legitimate.
    
    Args:
        email (str): The email address to validate.
        
    Returns:
        bool: True if the email is legitimate, False otherwise.
    """
    pattern = r"^[a-zA-Z0-9-_.]+@[a-zA-Z0-9-]+\.[a-z]{2,4}$"

    if re.match(pattern, email):
        return True
    return False

def generate_verification_token():
    """
    Generate a secure random token for email verification
    
    Returns:
        str: A secure random token
    """
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    # Initialize EmailPublisher
    publisher = EmailPublisher(Config.MAIL_USERNAME, 
                             Config.MAIL_PASSWORD
                             )
    
    # Set email subject and recipients
    subject = 'Test Email'
    recipients = ["mkaoy2k@me.com"]
    text = "This is a test email"
    html = r"""
    <style>
        .publish-message {
            font-size: 24px;
            font-weight: bold;
            color: #1f77b4;
        }
    </style>
    <div class="publish-message">
    <p>Your article has been approved and published:</p>
    </div>
    """
    # Send email
    if publisher.publish_email(subject, text, html, recipients):
        log.info("Email sent successfully")
    else:
        log.error("Failed to send email")
    