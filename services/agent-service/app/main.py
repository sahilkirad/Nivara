from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.init_db import init_db
from app.events.kafka_consumer import AgentContextEventConsumer


context_event_consumer = AgentContextEventConsumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await context_event_consumer.start()

    try:
        yield
    finally:
        await context_event_consumer.stop()


app = FastAPI(
    title="Nivara Agent Service",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {
        "service": settings.service_name,
        "status": "healthy",
        "environment": settings.environment,
    }