Phishing Simulation Tool - Instructions
=======================================

1. Setup
--------
- Install Python packages:
    pip install flask requests

- Fill in your SMTP email credentials in `config.py`.

2. Running the Server
---------------------
- Run the Flask server:
    python app.py

3. Sending Emails
-----------------
- Visit http://localhost:5000/send_emails to send test phishing emails.

4. Tracking Clicks
------------------
- When a user clicks the link, their info (IP, user-agent, geo location) is logged.

5. Viewing Report
-----------------
- Visit http://localhost:5000/report to view a summary of who clicked and where.

6. Notes
--------
- Modify the `test_users` dict in app.py with real test emails.


