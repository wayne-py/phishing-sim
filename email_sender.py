import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD, TRACKING_URL

def send_phishing_email(to_email, user_id, reason):
    link = f"{TRACKING_URL}?user={user_id}"

    subject = f"Urgent Action Required - {reason}"
    body = f"""
    <html>
        <body>
            <p>Dear {user_id},</p>
            <p>Please review the following issue immediately:</p>
            <p><a href="{link}">View Details</a></p>
            <p>Regards,<br>IT Security Team</p>
        </body>
    </html>
    """

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
