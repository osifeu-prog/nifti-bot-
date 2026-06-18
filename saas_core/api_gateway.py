from fastapi import FastAPI
from saas_core.db_manager import DBManager

app = FastAPI(title='NIFTI SAAS API')
db = DBManager()

@app.on_event('startup')
async def startup():
    await db.connect()

@app.get('/health')
async def health():
    return {'status': 'online', 'service': 'saas_core'}

@app.get('/user/{user_id}')
async def get_user(user_id: int):
    user = await db.get_user_data(user_id)
    return user if user else {'error': 'User not found'}
