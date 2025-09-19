from typing import List, Optional, Dict, Any
from pydantic import BaseModel


#--------------------------------------

class AccountBase(BaseModel):
    name: str
    contact_number: Optional[str] = None

class AccountCreate(AccountBase):
    password: str  # plain text from client, only for requests
    
class AccountIn(BaseModel):
    name: str
    password: str
    contact_number: str | None = None

class AccountOut(AccountBase):
    id: int
    class Config:
        # Pydantic v2:
        from_attributes = True
        # If you're on Pydantic v1, use:
        # orm_mode = True
    
#------------------------------------------

class SignupIn(BaseModel):
    name: str
    password: str
    contact_number: str | None = None

class AuthReq(BaseModel):
    name: str
    password: str
    
class SignupReq(AuthReq):
    contact_number: Optional[str] = None

#-----------------------------------------

class LoginIn(BaseModel):
    name: str
    password: str
    
#-----------------------------------------

class UserOut(BaseModel):
    id: int
    name: str
    contact_number: Optional[str] = None

    class Config:
        orm_mode = True  # allows returning SQLAlchemy model objects directly
        
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








