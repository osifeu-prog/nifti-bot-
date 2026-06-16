from fastapi import APIRouter
from nifti_core import check_db_health, pool
import time

router = APIRouter()

@router.get("/db")
async def db_health():
    try:
        health = await check_db_health()
        return health
    except Exception as e:
        return {"status": "error", "detail": str(e)}
