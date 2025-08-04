from pydantic import BaseModel
from datetime import datetime


class TransactionCreate(BaseModel):
    from_account_number: str
    to_account_number: str
    amount: float
    reference: str | None = None


class TransactionInitiateResponse(BaseModel):
    transaction_id: int
    message: str = "OTP sent to your e-mail"      # no OTP field!

    class Config:
        orm_mode = True


class TransactionVerifyRequest(BaseModel):
    transaction_id: int
    otp_code: str


class TransactionOut(BaseModel):
    id: int
    from_account_number: str
    to_account_number: str
    amount: float
    reference: str | None
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True
