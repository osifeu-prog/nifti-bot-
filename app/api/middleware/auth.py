from app.core.auth.jwt import verify_token
from fastapi import Request, HTTPException

async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    user = verify_token(token.replace("Bearer ", ""))

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    request.state.user = user
    return await call_next(request)

