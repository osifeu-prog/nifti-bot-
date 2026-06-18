from fastapi import FastAPI, HTTPException
from saas_core.db_manager import DBManager

app = FastAPI(title='NIFTI SAAS API')
db = DBManager()

@app.on_event('startup')
async def startup():
    await db.connect()

@app.get('/wallet/{user_id}')
async def get_wallet(user_id: int):
    user_data = await db.get_user_wallet(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail='User not found')
    
    # נחזיר את כל הדיקשנרי כדי שנראה את שמות העמודות האמיתיים
    return dict(user_data)
