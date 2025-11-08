# app/db.py
import os
from urllib.parse import urlparse, quote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

def _from_mysql_public_url(pub: str) -> str:
    u = urlparse(pub)
    user = u.username or ""
    pwd  = u.password or ""
    host = u.hostname or ""
    port = u.port or 3306
    db   = u.path.lstrip("/")
    return f"mysql+pymysql://{quote(user)}:{quote(pwd)}@{host}:{port}/{db}"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pub = os.getenv("MYSQL_PUBLIC_URL")
    if pub:
        DATABASE_URL = _from_mysql_public_url(pub)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it in Render → Environment. "
        "Format: mysql+pymysql://USER:PASSWORD@HOST:PORT/DB"
    )

# Mask sensitive info in logs
masked = DATABASE_URL
try:
    s = masked.find("://")
    a = masked.rfind("@")
    if s != -1 and a != -1:
        masked = masked[: s + 3] + "***:***" + masked[a:]
except Exception:
    pass
print(f"[DB] Using {masked} (TLS via connect_args)")

# ---- SQLAlchemy setup ----
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("POOL_SIZE", "5")),
    pool_recycle=int(os.getenv("POOL_RECYCLE", "280")),
    connect_args={"ssl": {}}  # Railway public proxy requires TLS
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- Auto-create tables on startup ----
def init_db():
    """
    Automatically create all tables if they don't exist.
    Safe to call multiple times.
    """
    from app import models  # import models to register metadata
    print("[DB] Checking and creating missing tables if needed...")
    Base.metadata.create_all(bind=engine)
    print("[DB] Table creation check complete.")
