from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, JSON, Date
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserSQL(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    city = Column(String)
    created_at = Column(String) # ISO format string
    settings = Column(JSON)

    accounts = relationship("AccountSQL", back_populates="owner")

class AccountSQL(Base):
    __tablename__ = 'accounts'

    account_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    type = Column(String)
    currency = Column(String)
    balance = Column(Float)
    salary_amount = Column(Integer)
    status = Column(String)

    owner = relationship("UserSQL", back_populates="accounts")
    cards = relationship("CardSQL", back_populates="account")
    transactions = relationship("AccountTransactionSQL", back_populates="account")

class CardSQL(Base):
    __tablename__ = 'cards'

    card_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey('accounts.account_id'))
    masked_number = Column(String)
    status = Column(String)
    limit = Column(Integer)
    billing_day = Column(Integer)
    spending_profile = Column(String)
    current_spend = Column(Float)
    issue_date = Column(String)
    expiry_date = Column(String)
    last_bill_date = Column(String, nullable=True)

    account = relationship("AccountSQL", back_populates="cards")
    transactions = relationship("CardTransactionSQL", back_populates="card")

class AccountTransactionSQL(Base):
    __tablename__ = 'account_transactions'

    transaction_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey('accounts.account_id'))
    amount = Column(Float)
    date = Column(String)
    description = Column(String)
    category = Column(String)
    location = Column(String)
    type = Column(String)
    transfer_group_id = Column(String, nullable=True)

    account = relationship("AccountSQL", back_populates="transactions")

class CardTransactionSQL(Base):
    __tablename__ = 'card_transactions'

    transaction_id = Column(String, primary_key=True)
    card_id = Column(String, ForeignKey('cards.card_id'))
    amount = Column(Float)
    date = Column(String)
    description = Column(String)
    category = Column(String)
    location = Column(String)
    type = Column(String)

    card = relationship("CardSQL", back_populates="transactions")

class BankMetadataSQL(Base):
    __tablename__ = 'bank_metadata'
    
    key = Column(String, primary_key=True)
    value = Column(JSON)