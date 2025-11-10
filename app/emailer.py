import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@blindspot.local")

def send_reset_email(to_email: str, code: str):
    subject = "BlindSpot Password Reset Code"
    html_content = f"""
    <div style='font-family:sans-serif;'>
        <p>Your BlindSpot password reset code is:</p>
        <h2 style='color:#2b6cb0;'>{code}</h2>
        <p>This code will expire in 15 minutes.</p>
        <p>If you didn’t request a password reset, please ignore this message.</p>
    </div>
    """

    if not RESEND_API_KEY:
        print(f"[DEV EMAIL] To: {to_email}\nSubject: {subject}\n\n{html_content}")
        return

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            },
            timeout=10,
        )

        if resp.status_code == 200 or resp.status_code == 201:
            print(f"[EMAIL] Sent via Resend to {to_email}")
        else:
            print(f"[EMAIL ERROR] Resend returned {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
