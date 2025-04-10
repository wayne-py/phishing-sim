from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clicks.db'
db = SQLAlchemy(app)

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    reason = db.Column(db.String(500))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_email', methods=['POST'])
def send_email():
    recipients = request.form.get('emails').split(',')
    reason = request.form['reason']
    phishing_link = request.host_url + 'click?email={}&reason=' + reason

    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')

    for recipient in recipients:
        recipient = recipient.strip()
        msg = MIMEText(f"Please check this important update: {phishing_link.format(recipient)}")
        msg['Subject'] = 'Important Security Update'
        msg['From'] = email_address
        msg['To'] = recipient

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)

    return redirect(url_for('index'))

@app.route('/click')
def click():
    email = request.args.get('email')
    reason = request.args.get('reason')
    if email:
        click = Click(email=email, reason=reason)
        db.session.add(click)
        db.session.commit()
    return "This was a simulation. Please be cautious of suspicious emails."

@app.route('/report')
def report():
    clicks = Click.query.all()
    return render_template('report.html', clicks=clicks)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
