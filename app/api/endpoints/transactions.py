# app/api/endpoints/transactions.py
from __future__ import annotations

import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import db
from app.api.endpoints.auth import get_current_user, get_db
from app.models.account import BankAccount
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionInitiateResponse,
    TransactionOut,
    TransactionVerifyRequest,
)
from app.utils.otp import (
    create_and_store_otp,
    verify_otp,
    send_otp_email,          # ← NEW name only
)

log = logging.getLogger(__name__)
router = APIRouter()

# ────────────────────────── helpers ──────────────────────────
def _get_accounts(tx: TransactionCreate, db: Session, user):
    """Validate accounts and balances, return (src, dst)."""
    from_acc = str(tx.from_account_number)
    to_acc = str(tx.to_account_number)
    src = (
        db.query(BankAccount)
        .filter(
            BankAccount.account_number == from_acc,
            BankAccount.user_id == user.id,
        )
        .first()
    )
    # Destination can be any valid account (owned by any user)
    dst = (
        db.query(BankAccount)
        .filter(BankAccount.account_number == to_acc)
        .first()
    )

    if not src or not dst:
        raise HTTPException(404, detail="Account not found")
    if src.account_number == dst.account_number:
        raise HTTPException(400, detail="Source and destination cannot be the same")
    if tx.amount <= 0:
        raise HTTPException(400, detail="Amount must be positive")
    if src.balance < tx.amount:
        raise HTTPException(400, detail="Insufficient balance")
    return src, dst

# ───────────────── POST /transactions/initiate ──────────────
@router.post(
    "/initiate",
    response_model=TransactionInitiateResponse,
    status_code=201,
)
def initiate_transfer(
    payload: TransactionCreate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    src, dst = _get_accounts(payload, db, current_user)

    pending = Transaction(
        from_account_number=src.account_number,
        to_account_number=dst.account_number,
        amount=payload.amount,
        reference=payload.reference,
        status="pending",
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)

    otp_code = create_and_store_otp(pending.id)
    # send e-mail out of request/response cycle
    bg.add_task(send_otp_email, current_user.email, otp_code)

    return TransactionInitiateResponse(transaction_id=pending.id)

# ───────────────── POST /transactions/verify ────────────────
from app.utils.otp import (
    verify_otp,
    is_otp_locked,
    increment_otp_failures,
    reset_otp_failures,
)

@router.post("/verify", response_model=TransactionOut, status_code=200)
def verify_transfer(
    payload: TransactionVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tx_id = payload.transaction_id

    # 1️⃣ Check if this transaction is temporarily locked
    if is_otp_locked(tx_id):
        raise HTTPException(
            status_code=403,
            detail="Too many failed OTP attempts. This transaction is locked for 5 minutes."
        )

    # 2️⃣ Verify OTP
    if not verify_otp(tx_id, payload.otp_code):
        attempts, locked = increment_otp_failures(tx_id)
        if locked:
            raise HTTPException(
                status_code=403,
                detail="Transaction locked after 3 failed OTP attempts. Please try again later."
            )
        raise HTTPException(
            status_code=401,
            detail=f"Invalid OTP. Attempt {attempts}/3"
        )

    # 3️⃣ OTP is valid — clear failure count
    reset_otp_failures(tx_id)

    # 4️⃣ fetch transaction
    tx = db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(404, detail="Transaction not found")
    if tx.status != "pending":
        raise HTTPException(409, detail="Transaction already processed")

    src = db.query(BankAccount).filter_by(account_number=tx.from_account_number).first()
    dst = db.query(BankAccount).filter_by(account_number=tx.to_account_number).first()

    if src.user_id != current_user.id:
        raise HTTPException(403, detail="Not owner of source account")

    # 5️⃣ Perform the balance transfer
    try:
        src.balance -= tx.amount
        dst.balance += tx.amount
        tx.status = "completed"
        db.commit()
        db.refresh(tx)
        return tx
    except SQLAlchemyError as exc:
        db.rollback()
        log.exception("DB error completing transfer")
        raise HTTPException(500, detail="Database error") from exc


# ───────────────── GET /transactions/ ───────────────────────
@router.get("/", response_model=list[TransactionOut])
def list_my_transactions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    my_numbers = [
        acc.account_number
        for acc in db.query(BankAccount)
        .filter(BankAccount.user_id == current_user.id)
        .all()
    ]
    return (
        db.query(Transaction)
        .filter(
            (Transaction.from_account_number.in_(my_numbers))
            | (Transaction.to_account_number.in_(my_numbers))
        )
        .order_by(Transaction.timestamp.desc())
        .all()
    )
