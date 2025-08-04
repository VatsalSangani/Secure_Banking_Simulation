import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.account import AccountCreate, AccountOut
from app.models.account import BankAccount
from app.api.endpoints.auth import get_current_user, get_db

router = APIRouter()


# ─────────────────────────────────────────  Create Account
@router.post("/", response_model=AccountOut)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # If account number not provided, generate a unique one
    if not payload.account_number:
        for _ in range(5):  # Retry max 5 times for uniqueness
            number = f"{random.randint(10000000, 99999999)}"
            if not db.query(BankAccount).filter_by(account_number=number).first():
                break
        else:
            raise HTTPException(status_code=500, detail="Failed to generate unique account number.")
    else:
        number = payload.account_number
        # Optional: prevent duplicates even if user manually provided one
        if db.query(BankAccount).filter_by(account_number=number).first():
            raise HTTPException(status_code=400, detail="Account number already exists.")

    new_acc = BankAccount(
        user_id=current_user.id,
        account_number=number,
        account_type=payload.account_type,
        balance=0.0,
    )
    db.add(new_acc)
    db.commit()
    db.refresh(new_acc)
    return new_acc


# ─────────────────────────────────────────  Get all accounts
@router.get("/", response_model=list[AccountOut])
def get_accounts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()


# ─────────────────────────────────────────  Delete account
@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    acc = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.user_id == current_user.id)
        .first()
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    if acc.balance != 0:
        raise HTTPException(
            status_code=400,
            detail="Account balance must be zero before deletion"
        )

    # TODO: Add pending transaction check if needed

    db.delete(acc)
    db.commit()
