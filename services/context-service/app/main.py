from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(title="Nivara Context Service")


@app.get("/health")
def health_check():
    return {
        "service": settings.service_name,
        "status": "healthy",
        "environment": settings.environment,
    }