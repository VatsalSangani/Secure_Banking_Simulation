from pydantic import BaseModel
from typing import Optional, Literal

class AccountCreate(BaseModel):
    account_type: Literal["savings", "current"] = "savings"
    account_number: str

class AccountOut(BaseModel):
    id: int
    account_number: str
    account_type: str
    balance: float

    class Config:
        orm_mode = True

# ──────────────────────────────
# Deposit-related Schemas
# ──────────────────────────────

class DepositInitRequest(BaseModel):
    account_number: str
    amount: float

class DepositInitResponse(BaseModel):
    deposit_id: int
    message: str = "OTP sent to your e-mail"

class DepositConfirmRequest(BaseModel):
    deposit_id: int
    otp: str
