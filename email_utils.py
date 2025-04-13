import os
import smtplib
import datetime
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from urllib.parse import urljoin
from flask import url_for
from jinja2 import Template

# Configure logging
logger = logging.getLogger(__name__)

def send_phishing_email(app, template, target):
    """
    Send a phishing email to a target using the provided template using Gmail SMTP.
    
    Args:
        app: Flask application instance with mail settings
        template: EmailTemplate object containing email content
        target: Target object with recipient information
    
    Returns:
        bool: True if sent successfully, False otherwise
    
    Raises:
        ValueError: If Gmail credentials are not configured
        smtplib.SMTPException: If there's an error with SMTP communication
        Exception: For any other errors during email sending
    """
    with app.app_context():
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template.subject
        msg['From'] = formataddr((template.sender_name, template.sender_email))
        msg['To'] = target.email
        
        # Generate URLs for tracking
        tracking_url = urljoin(app.config['APP_URL'], url_for('landing', tracking_id=target.tracking_id))
        pixel_url = urljoin(app.config['APP_URL'], url_for('track_open', tracking_id=target.tracking_id))
        
        # Render content with template variables
        content_template = Template(template.content)
        content_html = content_template.render(
            first_name=target.first_name,
            last_name=target.last_name,
            email=target.email,
            tracking_url=tracking_url,
            current_year=datetime.datetime.utcnow().year
        )
        
        # Add tracking pixel
        tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none;">'
        content_html += tracking_pixel
        
        # Attach HTML part
        html_part = MIMEText(content_html, 'html')
        msg.attach(html_part)
        
        # Connect to Gmail SMTP server and send
        try:
            # Configure for Gmail specifically
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
            # Use Gmail credentials from environment variables
            gmail_user = app.config['MAIL_USERNAME']
            gmail_password = app.config['MAIL_PASSWORD']
            
            if not gmail_user or not gmail_password:
                app.logger.error("Gmail credentials not configured")
                raise ValueError("Gmail credentials not configured. Please set GMAIL_USER and GMAIL_PASSWORD environment variables.")
            
            # Attempt login and send
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
            server.quit()
            
            app.logger.info(f"Email successfully sent to {target.email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "Gmail authentication failed. If you have 2-step verification enabled, use an App Password instead of your regular password."
            app.logger.error(error_msg)
            raise ValueError(error_msg)
            
        except smtplib.SMTPException as e:
            app.logger.error(f"SMTP error sending email to {target.email}: {str(e)}")
            raise
            
        except Exception as e:
            app.logger.error(f"Failed to send email to {target.email}: {str(e)}")
            raise