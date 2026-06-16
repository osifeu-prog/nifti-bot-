from fastapi import APIRouter

router = APIRouter(prefix="/admin")

@router.get("/ping")
def ping():
    return {"status": "admin online"}

