# app/main.py
import os, base64, io
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from PIL import Image
import jwt  # PyJWT

from .detector_ssd import get_detector

# DB + models + auth helpers
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from . import models, crud, schemas, auth
from .models import Account

# ------------ App & CORS ------------
app = FastAPI(
    title="BlindSpot API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

CORS_ALLOW = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if CORS_ALLOW == "*" else [o.strip() for o in CORS_ALLOW.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")

# ------------ Health ------------
@app.get("/health")
def health():
    return {"ok": True}

# =========================================================
# Auth Routes
# =========================================================
@app.post("/auth/signup", response_model=schemas.AuthRes)
def signup(body: schemas.SignupReq, db: Session = Depends(get_db)):
    if crud.get_account_by_name(db, body.name):
        raise HTTPException(status_code=409, detail="Account already exists")

    acc: Account = crud.create_account(
        db,
        name=body.name,
        password=body.password,
        contact_number=body.contact_number,
    )

    token = auth.make_token(acc.fld_ID)
    return {
        "token": token,
        "user": {
            "id": acc.fld_ID,
            "name": acc.fld_Name,
            "contact_number": acc.fld_ContactNumber,
        },
    }

@app.post("/auth/login", response_model=schemas.AuthRes)
def login(body: schemas.LoginReq, db: Session = Depends(get_db)):
    acc: Account | None = crud.get_account_by_name(db, body.name)
    if not acc or not auth.verify_pw(body.password, acc.fld_Password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.make_token(acc.fld_ID)
    return {
        "token": token,
        "user": {
            "id": acc.fld_ID,
            "name": acc.fld_Name,
            "contact_number": acc.fld_ContactNumber,
        },
    }

# =========================================================
# /me helpers & routes
# =========================================================
from fastapi import Header

def _current_account(db: Session, authorization: str = Header(..., alias="Authorization")) -> Account:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, auth.JWT_SECRET, algorithms=[auth.JWT_ALG])
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    acc = db.query(Account).filter(Account.fld_ID == uid).first()
    if not acc:
        raise HTTPException(status_code=404, detail="User not found")
    return acc

@app.get("/me", response_model=schemas.AccountOut)
def me(authorization: str = Header(..., alias="Authorization"), db: Session = Depends(get_db)):
    acc = _current_account(db, authorization)
    return {"id": acc.fld_ID, "name": acc.fld_Name, "contact_number": acc.fld_ContactNumber}

@app.put("/me", response_model=schemas.AccountOut)
def update_me(
    body: UpdateMeReq,
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db),
):
    acc = _current_account(db, authorization)
    if body.name is not None and body.name != acc.fld_Name:
        if db.query(Account).filter(Account.fld_Name == body.name).first():
            raise HTTPException(status_code=409, detail="Username already taken")
        acc.fld_Name = body.name
    if body.contact_number is not None:
        acc.fld_ContactNumber = body.contact_number
    db.add(acc); db.commit(); db.refresh(acc)
    return {"id": acc.fld_ID, "name": acc.fld_Name, "contact_number": acc.fld_ContactNumber}


# =========================================================
# Detection Routes
# =========================================================
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

class Box(BaseModel):
    x: float; y: float; w: float; h: float

class Detection(BaseModel):
    class_id: int
    class_name: str
    conf: float
    box: Box

class DetectResponse(BaseModel):
    time_ms: float
    detections: list[Detection]
    image_b64: str | None = None

@app.post("/detect", response_model=DetectResponse)
async def detect(file: UploadFile = File(...), return_image: bool = False):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Send JPEG/PNG/WEBP image")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image too large (max 5 MB)")
    pil = Image.open(io.BytesIO(raw)).convert("RGB")
    dets, jpeg_bytes, elapsed_ms = get_detector().infer(pil, return_image=return_image)

    b64 = None
    if return_image and jpeg_bytes:
        b64 = "data:image/jpeg;base64," + base64.b64encode(jpeg_bytes).decode("utf-8")
    return DetectResponse(time_ms=elapsed_ms, detections=dets, image_b64=b64)

