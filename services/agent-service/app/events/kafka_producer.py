import json
from typing import Any

from aiokafka import AIOKafkaProducer


class KafkaEventProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=self._serialize_value,
            key_serializer=self._serialize_key,
        )
        await self.producer.start()

    async def stop(self) -> None:
        if self.producer:
            await self.producer.stop()

    async def publish(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
    ) -> None:
        if not self.producer:
            raise RuntimeError("Kafka producer is not initialized.")

        await self.producer.send_and_wait(
            topic=topic,
            value=value,
            key=key,
        )

    def _serialize_value(self, value: dict[str, Any]) -> bytes:
        return json.dumps(value, default=str).encode("utf-8")

    def _serialize_key(self, key: str | None) -> bytes | None:
        if key is None:
            return None

        return key.encode("utf-8")