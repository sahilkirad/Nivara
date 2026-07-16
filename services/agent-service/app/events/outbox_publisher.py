import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from app.core.config import settings
from app.db.models import DeadLetterEvent, OutboxEvent
from app.db.session import SessionLocal
from app.events.contracts import EventEnvelope
from app.events.kafka_producer import KafkaEventProducer


logger = logging.getLogger(__name__)


RETRYABLE_OUTBOX_STATUSES = ("pending", "failed")


class OutboxPublisher:
    def __init__(self, producer: KafkaEventProducer):
        self.producer = producer
        self.task: asyncio.Task | None = None
        self.running = False

    async def start(self) -> None:
        self.running = True
        self.task = asyncio.create_task(self._publish_loop())

    async def stop(self) -> None:
        self.running = False

        if self.task:
            self.task.cancel()

            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _publish_loop(self) -> None:
        while self.running:
            try:
                await self.publish_pending_events()
            except Exception as exc:
                logger.exception("Outbox publisher loop failed: %s", exc)

            await asyncio.sleep(settings.outbox_publish_interval_seconds)

    async def publish_pending_events(self) -> None:
        db = SessionLocal()

        try:
            events = (
                db.query(OutboxEvent)
                .filter(OutboxEvent.published.is_(False))
                .filter(OutboxEvent.status.in_(RETRYABLE_OUTBOX_STATUSES))
                .filter(OutboxEvent.retry_count < settings.max_outbox_retry_count)
                .order_by(OutboxEvent.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(settings.outbox_batch_size)
                .all()
            )

            for event in events:
                await self._publish_single_event(db, event)

        finally:
            db.close()

    async def _publish_single_event(self, db, event: OutboxEvent) -> None:
        try:
            envelope = self._build_event_envelope(event)

            await self.producer.publish(
                topic=settings.agent_events_topic,
                value=envelope.model_dump(mode="json"),
                key=str(event.aggregate_id) if event.aggregate_id else None,
            )

            event.published = True
            event.status = "published"
            event.published_at = datetime.now(timezone.utc)
            event.last_error = None
            db.commit()

        except Exception as exc:
            db.rollback()
            await self._handle_publish_failure(db, event.id, str(exc))

    async def _handle_publish_failure(self, db, event_id, error_message: str) -> None:
        event = db.get(OutboxEvent, event_id)

        if not event:
            logger.error("Outbox event %s was not found after publish failure.", event_id)
            return

        next_retry_count = (event.retry_count or 0) + 1

        event.retry_count = next_retry_count
        event.last_error = error_message
        event.published = False

        if next_retry_count >= settings.max_outbox_retry_count:
            event.status = "dead_lettered"

            dead_letter_event = DeadLetterEvent(
                source_event_id=event.id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                correlation_id=event.correlation_id,
                source_service=settings.service_name,
                target_topic=settings.agent_events_topic,
                failure_stage="kafka_publish",
                retry_count=next_retry_count,
                last_error=error_message,
                payload=event.payload,
                status="dead_lettered",
            )

            db.add(dead_letter_event)

            logger.error(
                "Outbox event %s moved to dead letter after %s retries.",
                event.id,
                next_retry_count,
            )

        else:
            event.status = "failed"

            logger.exception(
                "Failed to publish outbox event %s. Retry count: %s",
                event.id,
                next_retry_count,
            )

        db.add(event)
        db.commit()

    def _build_event_envelope(self, event: OutboxEvent) -> EventEnvelope:
        payload = event.payload or {}
        customer_id = payload.get("customer_id")

        return EventEnvelope(
            event_id=self._to_uuid(event.id),
            correlation_id=self._to_uuid(event.correlation_id),
            customer_id=self._to_uuid(customer_id) if customer_id else None,
            event_type=event.event_type,
            source_service=settings.service_name,
            payload=payload,
        )

    def _to_uuid(self, value) -> UUID:
        return value if isinstance(value, UUID) else UUID(str(value))