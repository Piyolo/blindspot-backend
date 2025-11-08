# app/main.py
import os, base64, io
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from PIL import Image
import jwt  # PyJWT

from datetime import datetime, timedelta
import secrets
from .emailer import send_reset_email  # will create this file below

from .detector_ssd import get_detector

# DB + models + auth helpers
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from . import models, crud, schemas, auth
from .models import Account
from .schemas import UpdateMeReq, ReverifyReq, ReverifyRes
from .auth import verify_pw

bearer_scheme = HTTPBearer(auto_error=True)
bearer = HTTPBearer()
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

from .db import init_db  # import the helper from db.py

@app.on_event("startup")
def on_startup():
    init_db()  # this safely auto-creates missing tables


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
        email=body.email,  # NEW
    )

    token = auth.make_token(acc.fld_ID)
    return {
        "token": token,
        "user": {
            "id": acc.fld_ID,
            "name": acc.fld_Name,
            "contact_number": acc.fld_ContactNumber,
            "email": acc.fld_Email,  # optional return
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

@app.post("/auth/logout", status_code=204)
def logout(creds: HTTPAuthorizationCredentials = Security(bearer)):
    # Revoke current token (best effort). Client still clears local token.
    auth.revoke_token(creds.credentials)
    return


# =========================================================
# /me helpers & routes
# =========================================================

def _current_account(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """
    Reads the Authorization header via HTTP Bearer security,
    decodes the JWT, and loads the Account from MySQL.
    """
    token = creds.credentials  # Swagger will send only the token; scheme is 'Bearer'
    try:
        payload = jwt.decode(token, auth.JWT_SECRET, algorithms=[auth.JWT_ALG])
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    acc = db.query(Account).filter(Account.fld_ID == uid).first()
    if not acc:
        raise HTTPException(status_code=404, detail="User not found")
    return acc

# =========================================================
# /auth/reverify – confirm password for sensitive actions
# =========================================================
@app.post("/auth/reverify", response_model=ReverifyRes)
def reverify(
    body: ReverifyReq,
    acc: Account = Depends(_current_account)
):
    print("Reverify:", repr(body.password))
    print("Stored:", repr(acc.fld_Password))

    if not verify_pw(body.password, acc.fld_Password):
        print("bcrypt.checkpw returned False")
        raise HTTPException(status_code=401, detail="Invalid password")
    print("bcrypt.checkpw returned True")
    return {"authorized": True}

# =========================================================
# /auth/forgot – request password reset
# =========================================================
@app.post("/auth/forgot", response_model=schemas.ForgotRes)
def forgot_password(body: schemas.ForgotReq, db: Session = Depends(get_db)):
    # Try to find user by email or username
    acc = None
    if body.email:
        acc = crud.get_account_by_email(db, body.email)
    if not acc and body.username:
        acc = crud.get_account_by_name(db, body.username)

    # Always respond OK to prevent user enumeration
    if not acc or not acc.fld_Email:
        return {"message": "If the account exists, a reset link has been sent."}

    # Generate reset code and store it
    from .models import PasswordReset
    code = secrets.token_urlsafe(24)[:48]
    expires = datetime.utcnow() + timedelta(minutes=15)

    reset = PasswordReset(user_id=acc.fld_ID, code=code, expires_at=expires)
    db.add(reset)
    db.commit()

    try:
        send_reset_email(acc.fld_Email, code)
    except Exception as e:
        print("[WARN] Email send failed:", e)

    return {"message": "If the account exists, a reset link has been sent."}


# =========================================================
# /auth/reset – complete password reset
# =========================================================
@app.post("/auth/reset", response_model=schemas.ForgotRes)
def reset_password(body: schemas.ResetReq, db: Session = Depends(get_db)):
    from .models import PasswordReset
    now = datetime.utcnow()

    reset = (
        db.query(PasswordReset)
        .filter(
            PasswordReset.code == body.code,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > now,
        )
        .first()
    )

    if not reset:
        return {"message": "Password has been reset if the code was valid."}

    acc = db.query(Account).filter(Account.fld_ID == reset.user_id).first()
    if not acc:
        return {"message": "Password has been reset if the code was valid."}

    # Update password
    acc.fld_Password = auth.hash_pw(body.new_password)
    reset.used_at = now
    db.commit()

    return {"message": "Password reset successful."}

@app.get("/me", response_model=schemas.AccountOut)
def me(acc: Account = Depends(_current_account)):
    return {
        "id": acc.fld_ID,
        "name": acc.fld_Name,
        "contact_number": acc.fld_ContactNumber,
        "has_password": True,
        "password_len": len(acc.fld_Password) if acc.fld_Password else None
    }

@app.put("/me", response_model=schemas.AccountOut)
def update_me(
    body: UpdateMeReq, 
    acc: Account = Depends(_current_account), 
    db: Session = Depends(get_db)
):
    # Update name (ensure unique if changed)
    if body.name is not None and body.name != acc.fld_Name:
        if db.query(Account).filter(Account.fld_Name == body.name).first():
            raise HTTPException(status_code=409, detail="Username already taken")
        acc.fld_Name = body.name

    # Update contact number (None allowed to clear)
    if body.contact_number is not None:
        acc.fld_ContactNumber = body.contact_number

    # NEW: Update password (hash it)
    if body.password is not None and body.password.strip():
        acc.fld_Password = auth.hash_pw(body.password.strip())

    db.add(acc)
    db.commit()
    db.refresh(acc)

    return {
        "id": acc.fld_ID,
        "name": acc.fld_Name,
        "contact_number": acc.fld_ContactNumber,
        "has_password": True,                # you likely always have one after signup
        "password_len": len(acc.fld_Password) if acc.fld_Password else None
        
    }

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















