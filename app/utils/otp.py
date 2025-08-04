import os
import random
import smtplib
from email.message import EmailMessage
from typing import Final
import redis

# Redis config
REDIS_URL: Final = os.getenv("REDIS_URL", "redis://redis:6379/0")
OTP_TTL_SECONDS: Final = int(os.getenv("OTP_TTL_SECONDS", 300))  # 5 min default
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Email config
SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM", "SecureBank <no-reply@example.com>")

DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# ─────────────────────────────
# Redis key helpers
# ─────────────────────────────
def _key(tx_id: int) -> str:
    return f"otp:tx:{tx_id}"

def _fail_key(scope_id: str | int) -> str:
    return f"otp:fail:{scope_id}"

def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"

# ─────────────────────────────
# Public API — OTP Flow
# ─────────────────────────────
def create_and_store_otp(tx_id: int) -> str:
    code = _generate_otp()
    r.setex(_key(tx_id), OTP_TTL_SECONDS, code)

    if DEBUG_MODE:
        print(f"[DEV] OTP for tx {tx_id} = {code}")

    return code

def verify_otp(tx_id: int, submitted: str) -> bool:
    stored = r.get(_key(tx_id))
    if not stored or stored != submitted:
        return False
    r.delete(_key(tx_id))
    return True

def send_otp_email(to_addr: str, otp_code: str) -> None:
    if not SMTP_HOST or not to_addr:
        print("SMTP not configured properly.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Your SecureBank OTP"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_addr
    msg.set_content(f"Your OTP is: {otp_code}\nIt expires in {OTP_TTL_SECONDS // 60} minutes.")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            if SMTP_PORT != 1025:
                smtp.starttls()
                if SMTP_USER:
                    smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    except Exception as e:
        print(f"SMTP send failed: {e}")

# ─────────────────────────────
# OTP Failure + Lockout Logic
# ─────────────────────────────
def increment_otp_failures(scope_id: str | int, max_tries: int = 3, ttl: int = 300):
    """
    Increment OTP failure count. If max_tries exceeded, lock for TTL (seconds).
    Returns (current_count, is_locked).
    """
    key = _fail_key(scope_id)
    count = r.incr(key)
    if count == 1:
        r.expire(key, ttl)
    return count, count >= max_tries

def is_otp_locked(scope_id: str | int) -> bool:
    count = r.get(_fail_key(scope_id))
    return int(count or 0) >= 3

def reset_otp_failures(scope_id: str | int):
    r.delete(_fail_key(scope_id))
