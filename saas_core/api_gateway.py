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
    
    # מחזירים רק את מה שחשוב למשתמש בצורה נקייה
    return {
        'user_id': user_data.get('user_id'),
        'username': user_data.get('username'),
        'balance': user_data.get('balance'),
        'wallet_address': user_data.get('wallet')
    }
