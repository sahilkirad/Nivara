import asyncio
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import SessionLocal
from app.events.kafka_producer import KafkaEventProducer
from app.models import OutboxEvent


class OutboxPublisher:
    def __init__(self, producer: KafkaEventProducer) -> None:
        self.producer = producer
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        while self._running:
            await self.publish_pending_events()
            await asyncio.sleep(settings.outbox_publish_interval_seconds)

    async def publish_pending_events(self) -> None:
        db = SessionLocal()
        try:
            events = (
                db.query(OutboxEvent)
                .filter(OutboxEvent.published.is_(False))
                .order_by(OutboxEvent.created_at.asc())
                .limit(25)
                .all()
            )

            for event in events:
                await self._publish_one(event)

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def _publish_one(self, event: OutboxEvent) -> None:
        try:
            await self.producer.publish(settings.context_events_topic, event.payload)

            event.published = True
            event.published_at = datetime.now(timezone.utc)
            event.last_error = None
        except Exception as exc:
            event.retry_count += 1
            event.last_error = str(exc)