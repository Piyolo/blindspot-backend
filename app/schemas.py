from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# ---------- Accounts / Auth ----------

class AccountOut(BaseModel):
    id: int
    name: str
    contact_number: Optional[str] = None

    class Config:
        orm_mode = True

class AccountIn(BaseModel):
    # Used by your /accounts create route (if you keep it) and by signup
    name: str
    password: str
    contact_number: Optional[str] = None
    
class SignupReq(BaseModel):
    name: str
    password: str
    contact_number: Optional[str] = None

class LoginReq(BaseModel):
    name: str
    password: str

class AuthRes(BaseModel):
    token: str
    user: AccountOut

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










