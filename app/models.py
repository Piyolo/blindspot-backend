from sqlalchemy import Column, Integer, String, DateTime, func
from .db import Base

# Matches what you told me earlier (username-only, no email)
class Account(Base):
    __tablename__ = "tbl_accounts"
    fld_ID = Column(Integer, primary_key=True, autoincrement=True)
    fld_Name = Column(String(100), unique=True, nullable=False)          # username
    fld_Password = Column(String(255), nullable=False)                   # hashed
    fld_ContactNumber = Column(String(30), nullable=True)
    fld_AvatarImg = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
