import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD, TRACKING_URL

def send_phishing_email(to_address, user_id):
    with open('templates/email_template.html', 'r') as f:
        email_html = f.read().replace('{{TRACKING_LINK}}', f"{TRACKING_URL}{user_id}")

    msg = MIMEText(email_html, 'html')
    msg['Subject'] = 'Important Account Notice'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_address

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, [to_address], msg.as_string())
            print(f"Email sent to {to_address}")
    except Exception as e:
        print(f"Error sending email to {to_address}: {e}")
