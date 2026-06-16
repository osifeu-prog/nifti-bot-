from fastapi import FastAPI
from services.api.health import router as health_router
from services.api.ledger import router as ledger_router

app = FastAPI(title="NIFTI PRODUCTION CORE")

app.include_router(health_router)
app.include_router(ledger_router)

@app.get("/")
def root():
    return {
        "status": "NIFTI LIVE",
        "mode": "production"
    }