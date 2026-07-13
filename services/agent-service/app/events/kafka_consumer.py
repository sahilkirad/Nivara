import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import TopicPartition
from pydantic import ValidationError

from app.core.config import settings
from app.db.models import ProcessedEvent
from app.db.session import SessionLocal
from app.events.contracts import EventEnvelope
from app.workflows.agent_workflow import AgentWorkflow


logger = logging.getLogger(__name__)


class AgentContextEventConsumer:
    def __init__(self) -> None:
        self.consumer: AIOKafkaConsumer | None = None
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        self.consumer = AIOKafkaConsumer(
            settings.context_events_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.agent_consumer_group,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        await self.consumer.start()
        self.task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()

            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            await self.consumer.stop()

    async def _consume_loop(self) -> None:
        if not self.consumer:
            raise RuntimeError("Kafka consumer is not initialized.")

        async for message in self.consumer:
            await self._handle_message(message)

    async def _handle_message(self, message) -> None:
        if not self.consumer:
            raise RuntimeError("Kafka consumer is not initialized.")

        try:
            envelope = EventEnvelope.model_validate(message.value)
        except (ValidationError, TypeError, ValueError) as exc:
            logger.exception("Invalid Kafka event skipped: %s", exc)
            await self.consumer.commit()
            return

        if envelope.event_type != "customer.context.created":
            logger.info("Skipping unsupported event type: %s", envelope.event_type)
            await self.consumer.commit()
            return

        db = SessionLocal()

        try:
            already_processed = db.get(ProcessedEvent, envelope.event_id)

            if already_processed:
                await self.consumer.commit()
                return

            workflow = AgentWorkflow(db)
            workflow.run(
                event_payload=envelope.model_dump(mode="json"),
                source_event_id=str(envelope.event_id),
                correlation_id=str(envelope.correlation_id),
            )

            db.add(ProcessedEvent(
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                consumer_service=settings.service_name,
                status="processed",
            ))

            db.commit()
            await self.consumer.commit()

        except Exception as exc:
            db.rollback()
            logger.exception("Agent workflow failed; Kafka offset not committed: %s", exc)

            topic_partition = TopicPartition(message.topic, message.partition)
            self.consumer.seek(topic_partition, message.offset)
            await asyncio.sleep(settings.consumer_retry_backoff_seconds)

        finally:
            db.close()