from fastapi import FastAPI, Depends
from services.api.auth import verify_token
from services.api.health import router as health_router
from services.api.ledger import router as ledger_router

app = FastAPI(title="NIFTI STABLE API")

app.include_router(health_router, prefix="/health")
app.include_router(ledger_router, prefix="/ledger")

@app.get("/")
def root():
    return {"status": "NIFTI RUNNING"}
