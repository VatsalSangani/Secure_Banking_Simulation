# app/api/endpoints/otp.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.utils.otp import (
    create_and_store_otp,
    verify_otp,
    send_otp_email,
)
from app.api.endpoints.auth import get_current_user, get_db
from app.models.user import User

router = APIRouter(
    prefix="/otp",
    tags=["OTP"]
)

# ─────────────────────────────────────────────────────────────
# 1. Send (generate) OTP
# ─────────────────────────────────────────────────────────────
@router.post("/send", status_code=status.HTTP_200_OK)
def send_otp(
    db: Session = Depends(get_db),  #  kept for symmetry / future use
    current_user: User = Depends(get_current_user),
):
    """
    Generate a new OTP for the logged-in user, store it in Redis,
    and send it to their e-mail address.

    Returns just a success message (code never returned in prod).
    """
    code = create_and_store_otp(current_user.id)

    # ── DEV / PROD switch ───────────────────────────────────
    # In production, integrate a real e-mail service.
    send_otp_email(current_user.email, code)
    # -- for dev you might also return the code:
    # return {"otp": code}
    # --------------------------------------------------------

    return {"msg": "OTP sent to your e-mail"}

# ─────────────────────────────────────────────────────────────
# 2. Verify OTP
# ─────────────────────────────────────────────────────────────
class OTPVerifyRequest(BaseModel):
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")

@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_otp_endpoint(
    payload: OTPVerifyRequest,
    db: Session = Depends(get_db),          # kept for symmetry / future use
    current_user: User = Depends(get_current_user),
):
    """
    Verify a 6-digit OTP. 401 on failure, 200 on success.
    """
    # Will raise HTTPException(401) if invalid / expired
    verify_otp(current_user.id, payload.otp_code)

    return {"msg": "OTP verified successfully"}
