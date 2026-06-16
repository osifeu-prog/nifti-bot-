from fastapi import APIRouter
from core.db.engine import engine

router = APIRouter()

@router.get("/{user_id}")
def get_balance(user_id: int):
    # שינוי לפורמט בטוח של SQLAlchemy
    query = "SELECT balance FROM users WHERE id=:uid"
    result = engine.execute(query, {"uid": user_id}).fetchone()
    if not result:
        return {"user_id": user_id, "balance": 0}
    return {"user_id": user_id, "balance": float(result[0])}
