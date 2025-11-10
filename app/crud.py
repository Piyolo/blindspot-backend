from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models
from .auth import hash_pw


def create_account(db: Session, email: str, password: str, contact_number: str | None = None):
    acc = models.Account(
        fld_Email=email,
        fld_Password=hash_pw(password),
        fld_ContactNumber=contact_number,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def get_account_by_email(db: Session, email: str):
    return (
        db.query(models.Account)
        .filter(func.lower(models.Account.fld_Email) == email.lower())
        .first()
    )
