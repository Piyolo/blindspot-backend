from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

# Matches what you told me earlier (username-only, no email)
class Account(Base):
    __tablename__ = "tbl_accounts"
    
    fld_ID = Column(Integer, primary_key=True, autoincrement=True)
    fld_Email = Column(String(100), unique=True, nullable=False)          # username
    fld_Password = Column(String(255), nullable=False)                   # hashed
    fld_ContactNumber = Column(String(30), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    resets = relationship("PasswordReset", back_populates="user", cascade="all,delete-orphan")

class PasswordReset(Base):
    __tablename__ = "tbl_password_resets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("tbl_accounts.fld_ID"), nullable=False)
    code = Column(String(64), nullable=False, index=True)
    purpose = Column(String(32), nullable=False, default="reset")
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("Account", back_populates="resets")
