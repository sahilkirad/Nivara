from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.init_db import init_db
from app.events.kafka_consumer import AgentContextEventConsumer
from app.events.kafka_producer import KafkaEventProducer
from app.events.outbox_publisher import OutboxPublisher


context_event_consumer = AgentContextEventConsumer()
kafka_event_producer = KafkaEventProducer(settings.kafka_bootstrap_servers)
outbox_publisher = OutboxPublisher(kafka_event_producer)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    await kafka_event_producer.start()
    await outbox_publisher.start()
    await context_event_consumer.start()

    try:
        yield
    finally:
        await context_event_consumer.stop()
        await outbox_publisher.stop()
        await kafka_event_producer.stop()


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