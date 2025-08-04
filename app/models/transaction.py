from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_account_number = Column(String, ForeignKey("bank_accounts.account_number"), nullable=False)
    to_account_number = Column(String, ForeignKey("bank_accounts.account_number"), nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")  # values: completed, failed, pending

    from_account = relationship(
        "BankAccount",
        foreign_keys=[from_account_number],
        back_populates="outgoing_transactions"
    )

    to_account = relationship(
        "BankAccount",
        foreign_keys=[to_account_number],
        back_populates="incoming_transactions"
    )
