import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("mysql+pymysql://root:XnvkXwkokSHuNBUZIyYfoOPCjiIWFeFe@mysql.railway.internal:3306/railway?ssl=true")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("POOL_SIZE", "5")),
    pool_recycle=int(os.getenv("POOL_RECYCLE", "280")),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
