from sqlalchemy import Column, Integer, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    account_number = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(String, nullable=False, default="savings")
    balance = Column(Float, default=0.0)

    # Relationship to user
    owner = relationship("User", back_populates="accounts")

    
    outgoing_transactions = relationship(
        "Transaction",
        foreign_keys="[Transaction.from_account_number]",
        back_populates="from_account"
    )

    incoming_transactions = relationship(
        "Transaction",
        foreign_keys="[Transaction.to_account_number]",
        back_populates="to_account"
    )
