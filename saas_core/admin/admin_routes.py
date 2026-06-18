from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from saas_core.db_manager import db

router = APIRouter()
templates = Jinja2Templates(directory="saas_core/admin/templates")

@router.get("/admin")
async def admin_dashboard(request: Request):
    async with db.pool.acquire() as conn:
        premium_users = await conn.fetch("SELECT * FROM premium_users ORDER BY created_at DESC")
    return templates.TemplateResponse("dashboard.html", {"request": request, "users": premium_users})
