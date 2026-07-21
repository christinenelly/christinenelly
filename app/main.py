from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, condecimal
from decimal import Decimal, ROUND_DOWN
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from .database import SessionLocal, engine
from .models import Base, Account

Base.metadata.create_all(bind=engine)

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bank")

API_KEY = os.getenv("API_KEY", "devkey")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(title="Fast Bank Transfer")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")


class AccountCreate(BaseModel):
    owner: str
    initial_balance: condecimal(gt=-1)


class AccountOut(BaseModel):
    id: int
    owner: str
    balance: Decimal


class TransferIn(BaseModel):
    from_id: int
    to_id: int
    amount: condecimal(gt=0)


def to_cents(d: Decimal) -> int:
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_DOWN))


def from_cents(c: int) -> Decimal:
    return (Decimal(c) / Decimal(100)).quantize(Decimal("0.01"))


@app.get("/", response_class=HTMLResponse)
def index():
    try:
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Bank App</h1><p>No frontend installed.</p>")


@app.post("/accounts", response_model=AccountOut)
def create_account(payload: AccountCreate, api_key: str = Depends(get_api_key)):
    cents = to_cents(Decimal(payload.initial_balance))
    db = SessionLocal()
    try:
        acct = Account(owner=payload.owner, balance_cents=cents)
        db.add(acct)
        db.commit()
        db.refresh(acct)
        logger.info("Created account %s owner=%s balance=%s", acct.id, acct.owner, acct.balance_cents)
        return AccountOut(id=acct.id, owner=acct.owner, balance=from_cents(acct.balance_cents))
    finally:
        db.close()


@app.get("/accounts/{account_id}", response_model=AccountOut)
def get_account(account_id: int, api_key: str = Depends(get_api_key)):
    db = SessionLocal()
    try:
        acct = db.get(Account, account_id)
        if not acct:
            raise HTTPException(status_code=404, detail="Account not found")
        return AccountOut(id=acct.id, owner=acct.owner, balance=from_cents(acct.balance_cents))
    finally:
        db.close()


@app.post("/transfer")
def transfer(payload: TransferIn, api_key: str = Depends(get_api_key)):
    amount_cents = to_cents(Decimal(payload.amount))
    if payload.from_id == payload.to_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    db = SessionLocal()
    try:
        try:
            with db.begin():
                # subtract from sender only if sufficient funds
                res = db.execute(
                    update(Account)
                    .where(Account.id == payload.from_id)
                    .where(Account.balance_cents >= amount_cents)
                    .values(balance_cents=Account.balance_cents - amount_cents)
                )
                if res.rowcount != 1:
                    raise HTTPException(status_code=400, detail="Insufficient funds or sender not found")

                res2 = db.execute(
                    update(Account)
                    .where(Account.id == payload.to_id)
                    .values(balance_cents=Account.balance_cents + amount_cents)
                )
                if res2.rowcount != 1:
                    # recipient not found — trigger rollback
                    raise HTTPException(status_code=400, detail="Recipient account not found")

            # on success, return balances
            from_acct = db.get(Account, payload.from_id)
            to_acct = db.get(Account, payload.to_id)
            logger.info("Transfer %s -> %s cents=%s", payload.from_id, payload.to_id, amount_cents)
            return {
                "from": {"id": from_acct.id, "balance": from_cents(from_acct.balance_cents)},
                "to": {"id": to_acct.id, "balance": from_cents(to_acct.balance_cents)},
            }
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.exception("Database error during transfer")
            raise HTTPException(status_code=500, detail="Database error")
    finally:
        db.close()
