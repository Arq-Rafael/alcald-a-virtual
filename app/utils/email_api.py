"""Email API helpers (SendGrid) to avoid SMTP restrictions"""
import os
import requests

def send_email_sendgrid(api_key: str, from_email: str, to_email: str, subject: str, html_content: str) -> bool:
    """Send an email via SendGrid HTTP API.
    Returns True on 202 Accepted, else False.
    """
    if not api_key:
        return False
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}]
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        return resp.status_code == 202
    except Exception:
        return False
