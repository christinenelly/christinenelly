from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import declarative_base
from sqlalchemy import BigInteger

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    # store balances as integer cents to avoid floating point errors
    balance_cents = Column(BigInteger, nullable=False, default=0)
