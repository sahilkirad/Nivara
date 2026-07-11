from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
# When agent-service publishes AgentAnalysisCompleted, it will include:
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    customer_id: UUID | None = None
    event_type: str
    source_service: str = "agent-service"
    event_version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)