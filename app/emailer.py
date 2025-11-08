import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@blindspot.local")


def send_reset_email(to_email: str, code: str):
    subject = "BlindSpot Password Reset Code"
    body = (
        f"Your BlindSpot password reset code is:\n\n"
        f"{code}\n\n"
        f"This code expires in 15 minutes. "
        f"If you didn’t request a password reset, you can ignore this email."
    )

    # Debug print to verify env vars loaded
    print(
        f"[EMAIL DEBUG] HOST={SMTP_HOST}, USER={SMTP_USER}, "
        f"PASS={'set' if SMTP_PASS else 'missing'}"
    )

    # If any required variable is missing → run in dev mode
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        print(f"[DEV EMAIL] To: {to_email}\nSubject: {subject}\n\n{body}")
        return

    # ----- REAL EMAIL SENDING -----
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            print("[EMAIL] Connecting to Gmail SMTP...")
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            print("[EMAIL] Logged in to Gmail SMTP successfully.")

            msg = EmailMessage()
            msg["From"] = FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body)

            s.send_message(msg)
            print(f"[EMAIL] Message sent to {to_email}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
