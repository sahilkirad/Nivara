from fastapi import FastAPI

from app.api import onboarding_router
from app.core.config import settings
from app.db.init_db import init_db


app = FastAPI(title="Nivara Context Service")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(onboarding_router)


@app.get("/health")
def health_check():
    return {
        "service": settings.service_name,
        "status": "healthy",
        "environment": settings.environment,
    }