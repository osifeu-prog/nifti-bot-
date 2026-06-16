from fastapi import FastAPI
from core.ledger.ledger import Ledger

app = FastAPI(title="NIFTI API V1")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/ledger/{user_id}")
def get_balance(user_id: int):
    return {"balance": Ledger.get_balance(user_id)}

@app.post("/v1/ledger/add")
def add_balance(user_id: int, amount: float):
    Ledger.add_balance(user_id, amount)
    return {"status": "ok"}

