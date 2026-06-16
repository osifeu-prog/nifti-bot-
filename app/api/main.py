from fastapi import FastAPI
from app.api.routes import admin

app = FastAPI(title="NIFTI V16")

app.include_router(admin.router)

@app.get("/health")
def health():
    return {"status": "ok"}

