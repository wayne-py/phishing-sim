def send_phishing_email(to_email, user_id, reason):
    link = f"{TRACKING_URL}?user={user_id}"

    subject = f"Urgent Action Required - {reason}"
    body = f"""
    Dear {user_id},

    Please review the following issue immediately: <a href="{link}">View Details</a>.

    Regards,
    IT Security Team
    """

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
