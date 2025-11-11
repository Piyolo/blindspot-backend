# app/emailer.py
import os
import requests

# Use the Cloud Run service as the email sender
EMAIL_API_URL = os.getenv("EMAIL_API_URL", "").strip()
EMAIL_API_TOKEN = os.getenv("EMAIL_API_TOKEN", "").strip()  # Optional

def send_reset_email(to_email: str, code: str):
    """Send password reset email using the deployed Cloud Run service."""
    subject = "BlindSpot Password Reset Code"
    html = f"""
    <div style='font-family:sans-serif;'>
        <h2>Password Reset Request</h2>
        <p>Your BlindSpot reset code is:</p>
        <h1 style='color:#2b6cb0;'>{code}</h1>
        <p>This code will expire in 15 minutes.</p>
        <p>If you didn't request this, you can ignore this message.</p>
    </div>
    """

    # If no Cloud Run emailer configured, fallback to dev print
    if not EMAIL_API_URL:
        print(f"[DEV EMAIL] To: {to_email}\nSubject: {subject}\n{html}")
        return

    try:
        headers = {"Content-Type": "application/json"}
        if EMAIL_API_TOKEN:
            headers["Authorization"] = f"Bearer {EMAIL_API_TOKEN}"

        payload = {
            "to": to_email,
            "subject": subject,
            "html": html
        }

        resp = requests.post(EMAIL_API_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            print(f"[EMAIL] Sent via Cloud Run to {to_email}")
        else:
            print(f"[EMAIL ERROR] {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"[EMAIL ERROR] Exception: {e}")
