import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD, TRACKING_URL

def send_phishing_email(to_email, user_id, reason):
    # Load and personalize the HTML email template
    with open('templates/email_template.html', 'r') as f:
        template = f.read()
    
    link = f"{TRACKING_URL}?user={user_id}"
    email_html = template.replace("{{TRACKING_LINK}}", link)

    # Build the message
    subject = f"Urgent Action Required - {reason}"
    msg = MIMEText(email_html, 'html')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    # Send the email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
