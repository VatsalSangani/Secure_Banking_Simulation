from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.account import BankAccount
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate
from datetime import datetime

def create_transaction(db: Session, user_id: int, tx_data: TransactionCreate):
    # Fetch both accounts
    from_acc = db.query(BankAccount).filter(
        BankAccount.id == tx_data.from_account_id,
        BankAccount.user_id == user_id
    ).first()

    to_acc = db.query(BankAccount).filter(
        BankAccount.id == tx_data.to_account_id
    ).first()

    if not from_acc or not to_acc:
        raise HTTPException(status_code=404, detail="Invalid account(s)")

    if from_acc.id == to_acc.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    if from_acc.balance < tx_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Perform the transaction
    from_acc.balance -= tx_data.amount
    to_acc.balance += tx_data.amount

    transaction = Transaction(
        from_account_id=from_acc.id,
        to_account_id=to_acc.id,
        amount=tx_data.amount,
        reference=tx_data.reference,
        timestamp=datetime.utcnow(),
        status="completed"
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction
