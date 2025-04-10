
from flask import Flask, request, render_template
import sqlite3
import datetime
from email_sender import send_phishing_email
from config import TRACKING_URL

app = Flask(__name__)

def init_db():
    with sqlite3.connect('phish.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp TEXT,
            user_agent TEXT,
            ip_address TEXT,
            location TEXT
        )''')
        conn.commit()

@app.route('/')
def index():
    return '<h1>Phishing Simulator</h1><a href="/send_emails">Send Test Emails</a> | <a href="/report">View Report</a>'

@app.route('/send_emails')
def send_emails():
    test_users = {
        'user1@example.com': 'user1',
        'user2@example.com': 'user2',
    }
    for email, user_id in test_users.items():
        send_phishing_email(email, user_id)
    return 'Emails sent!'

@app.route('/track')
def track():
    import requests
    user_id = request.args.get('user')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    timestamp = datetime.datetime.now().isoformat()

    location = "Unknown"
    try:
        geo_req = requests.get(f'https://ipapi.co/{ip}/json/')
        if geo_req.ok:
            geo_data = geo_req.json()
            location = f"{geo_data.get('city', '')}, {geo_data.get('region', '')}, {geo_data.get('country_name', '')}"
    except:
        pass

    with sqlite3.connect('phish.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO clicks (user_id, timestamp, user_agent, ip_address, location) VALUES (?, ?, ?, ?, ?)',
                  (user_id, timestamp, user_agent, ip, location))
        conn.commit()
    return render_template('clicked.html', user_id=user_id)

@app.route('/report')
def report():
    with sqlite3.connect('phish.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM clicks')
        data = c.fetchall()

    suggestions = {
        'generic': "Don't click suspicious links. Verify email sources. Hover over links before clicking.",
    }
    return render_template('report.html', data=data, suggestions=suggestions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
