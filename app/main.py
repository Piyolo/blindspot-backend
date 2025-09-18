# app/main.py
import os, base64, io
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from fastapi import Response
from pydantic import BaseModel
from fastapi import UploadFile, File, HTTPException
from pydantic import BaseModel
from .detector_ssd import get_detector
from .auth import hash_pw, verify_pw, make_token, require_user
from .storage import (
    init_with_admin, create_account, get_account_by_name, get_user_by_email,
    get_emergency_contact, set_emergency_contact
)
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
# ------------ App & CORS ------------
IS_PROD = os.getenv("ENV") == "prod"
app = FastAPI(
    title="BlindSpot API (no DB)",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)

CORS_ALLOW = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if CORS_ALLOW == "*" else [o.strip() for o in CORS_ALLOW.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed an admin with empty password hash (optional)
init_with_admin("admin", "")

@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")
# ------------ Health ------------
@app.get("/health")
def health():
    return {"ok": True}

# ------------ Auth (OPTIONAL) ------------
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"

class SignupReq(BaseModel):
    name: str
    password: str

class LoginReq(BaseModel):
    name: str
    password: str

class AuthRes(BaseModel):
    token: str
    user_id: int
    name: str

if ENABLE_AUTH:
    @app.post("/auth/signup", response_model=AuthRes)
    def signup(req: SignupReq):
        if get_account_by_name(req.name):
            raise HTTPException(409, "username already exists")
        user = create_account(req.name, hash_pw(req.password))
        return {"token": make_token(user.id), "user_id": user.id, "name": user.name}

    @app.post("/auth/login", response_model=AuthRes)
    def login(req: LoginReq):
        user = get_user_by_email(req.name) or get_account_by_name(req.name)
        if not user or not verify_pw(req.password, user.password_hash):
            raise HTTPException(401, "invalid credentials")
        return {"token": make_token(user.id), "user_id": user.id, "name": user.name}

# ------------ Contacts (OPTIONAL; requires auth) ------------
class ContactReq(BaseModel):
    contact_number: str | None

class ContactRes(BaseModel):
    contact_number: str | None

if ENABLE_AUTH:
    @app.get("/contacts/me", response_model=ContactRes)
    def get_me(user=Depends(require_user)):
        return {"contact_number": get_emergency_contact(user.id)}

    @app.put("/contacts/me", response_model=ContactRes)
    def set_me(req: ContactReq, user=Depends(require_user)):
        set_emergency_contact(user.id, req.contact_number)
        return {"contact_number": req.contact_number}

# ------------ Detection (public or secure—your choice) ------------
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
