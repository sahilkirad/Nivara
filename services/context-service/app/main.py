from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import onboarding_router
from app.core.config import settings
from app.db.init_db import init_db
from app.events import KafkaEventProducer, OutboxPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    producer = KafkaEventProducer()
    await producer.start()

    outbox_publisher = OutboxPublisher(producer)
    await outbox_publisher.start()

    app.state.kafka_producer = producer
    app.state.outbox_publisher = outbox_publisher

    try:
        yield
    finally:
        await outbox_publisher.stop()
        await producer.stop()


app = FastAPI(title="Nivara Context Service", lifespan=lifespan)

app.include_router(onboarding_router)


@app.get("/health")
def health_check():
    return {
        "service": settings.service_name,
        "status": "healthy",
        "environment": settings.environment,
    }