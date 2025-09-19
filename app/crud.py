from sqlalchemy.orm import Session
from . import models
from .auth import hash_pw  # reuse yours

def create_account(db: Session, name: str, password: str, contact_number: str | None):
    acc = models.Account(
        fld_Name=name,
        fld_Password=hash_pw(password),
        fld_ContactNumber=contact_number,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

def get_account_by_name(db: Session, name: str):
    return db.query(models.Account).filter(models.Account.fld_Name == name).first()
