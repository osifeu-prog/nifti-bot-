from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, os, datetime

SECRET = os.getenv("JWT_SECRET", "super-secret-key")
ALGORITHM = "HS256"

def create_token(user_id: int):
    payload = {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
