from typing import List, Optional, Dict, Any
from pydantic import BaseModel



class AccountIn(BaseModel):
    name: str
    password: str
    contact_number: str | None = None

class AccountOut(BaseModel):
    name: str
    password: str
    contact_number: str | None

class SignupIn(BaseModel):
    name: str
    password: str
    contact_number: str | None = None

class LoginIn(BaseModel):
    name: str
    password: str

class AuthRes(BaseModel):
    token: str
    user: AccountOut
    
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



