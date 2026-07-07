from fastapi import FastAPI

from app.core.config import settings
from app.db.init_db import init_db


app = FastAPI(title="Nivara Context Service")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check():
    return {
        "service": settings.service_name,
        "status": "healthy",
        "environment": settings.environment,
    }