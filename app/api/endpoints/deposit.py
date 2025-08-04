from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.endpoints.auth import get_current_user, get_db
from app.models.account import BankAccount
from app.models.deposit import Deposit
from app.utils.otp import (
    create_and_store_otp,
    send_otp_email,
    verify_otp,
    is_otp_locked,
    increment_otp_failures,
    reset_otp_failures,
)
from app.schemas.account import (
    DepositInitRequest,
    DepositInitResponse,
    DepositConfirmRequest,
)

router = APIRouter(prefix="/deposit", tags=["Deposit"])

@router.post("/initiate", response_model=DepositInitResponse)
def initiate_deposit(
    payload: DepositInitRequest,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    acc = db.query(BankAccount).filter_by(
        account_number=payload.account_number,
        user_id=current_user.id
    ).first()

    if not acc:
        raise HTTPException(404, detail="Account not found")

    deposit = Deposit(
        user_id=current_user.id,
        account_number=payload.account_number,
        amount=payload.amount,
        status="pending"
    )
    db.add(deposit)
    db.commit()
    db.refresh(deposit)

    otp = create_and_store_otp(deposit.id)
    bg.add_task(send_otp_email, current_user.email, otp)

    return DepositInitResponse(deposit_id=deposit.id)

@router.post("/confirm")
def confirm_deposit(
    payload: DepositConfirmRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deposit = db.get(Deposit, payload.deposit_id)

    if not deposit or deposit.user_id != current_user.id:
        raise HTTPException(404, detail="Deposit not found")

    if deposit.status != "pending":
        raise HTTPException(409, detail="Deposit already processed")

    if is_otp_locked(deposit.id):
        raise HTTPException(403, detail="Too many failed attempts. Try again in 5 minutes.")

    if not verify_otp(deposit.id, payload.otp):
        attempts, locked = increment_otp_failures(deposit.id)
        if locked:
            raise HTTPException(403, detail="Deposit locked after 3 failed OTP attempts.")
        raise HTTPException(401, detail=f"Invalid OTP. Attempt {attempts}/3")

    reset_otp_failures(deposit.id)

    acc = db.query(BankAccount).filter_by(
        account_number=deposit.account_number,
        user_id=current_user.id
    ).first()

    if not acc:
        raise HTTPException(404, detail="Account not found")

    acc.balance += deposit.amount
    deposit.status = "completed"
    db.commit()

    return {"msg": "Deposit successful", "new_balance": acc.balance}
