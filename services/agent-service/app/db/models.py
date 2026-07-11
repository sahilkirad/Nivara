from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_event_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    correlation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="completed")
    life_events: Mapped[dict] = mapped_column(JSONB, nullable=False)
    needs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    mapped_services: Mapped[dict] = mapped_column(JSONB, nullable=False)
    explainability: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EpisodicMemory(Base):
    __tablename__ = "episodic_memory"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(80), default="episodic")
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SemanticMemory(Base):
    __tablename__ = "semantic_memory"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    knowledge_type: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    consumer_service: Mapped[str] = mapped_column(String(120), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    status: Mapped[str] = mapped_column(String(40), default="processed")


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregate_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    correlation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)