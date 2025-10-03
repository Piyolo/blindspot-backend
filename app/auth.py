import os, bcrypt, jwt, datetime, uuid
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .storage import get_account_by_id

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")  # set in .env for prod
JWT_ALG = "HS256"
bearer = HTTPBearer()

BLACKLIST = set()

def hash_pw(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

def verify_pw(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode(), h.encode())

def make_token(user_id: int) -> str:
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id, 
        "jti": jti,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def require_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        jti = payload.get("jti")
        if jti in BLACKLIST:
            raise HTTPException(status_code=401, detail="Token revoked")
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_account_by_id(uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def revoke_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], options={"verify_exp": False})
        jti = payload.get("jti")
        if jti:
            BLACKLIST.add(jti)
    except Exception:
        pass


