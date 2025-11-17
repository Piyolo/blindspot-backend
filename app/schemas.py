from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr


# ---------- Accounts / Auth ----------

class AccountOut(BaseModel):
    id: int
    email: str
    contact_number: Optional[str] = None
    has_password: bool = True           # NEW
    password_len: Optional[int] = None  # OPTIONAL: if you really want dynamic bullet count

    class Config:
        orm_mode = True

class AccountIn(BaseModel):
    # Used by your /accounts create route (if you keep it) and by signup
    email: str
    password: str
    contact_number: Optional[str] = None
    
class SignupReq(BaseModel):
    email: str
    password: str
    contact_number: Optional[str] = None

class LoginReq(BaseModel):
    email: str
    password: str

class AuthRes(BaseModel):
    token: str
    user: AccountOut


class UpdateMeReq(BaseModel):
    email: Optional[str] = None
    contact_number: Optional[str] = None
    password: Optional[str] = None

# Reverify
class ReverifyReq(BaseModel):
    password: str

class ReverifyRes(BaseModel):
    authorized: bool

class ForgotReq(BaseModel):
    email: Optional[EmailStr] = None

class ForgotRes(BaseModel):
    message: str

class ResetReq(BaseModel):
    code: str
    new_password: str

class CheckUserReq(BaseModel):
    email: str  # this is your username

class CheckUserRes(BaseModel):
    exists: bool

class SimpleResetReq(BaseModel):
    email: str      # username
    new_password: str

#-----------------------------------------
class Box(BaseModel):
    x: float; y: float; w: float; h: float

class Detection(BaseModel):
    class_id: int
    class_name: str
    conf: float
    box: Box

class DetectResponse(BaseModel):
    time_ms: float
    detections: List[Detection]
    image_b64: Optional[str] = None  # data:image/jpeg;base64,...


















