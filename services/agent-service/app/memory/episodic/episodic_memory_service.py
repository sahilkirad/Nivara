from sqlalchemy.orm import Session

from app.db.models import EpisodicMemory


class EpisodicMemoryService:
    def __init__(self, db: Session):
        self.db = db

    def load_customer_memory(self, customer_id: str | None) -> list[dict]:
        if not customer_id:
            return []

        rows = (
            self.db.query(EpisodicMemory)
            .filter(EpisodicMemory.customer_id == customer_id)
            .order_by(EpisodicMemory.created_at.desc())
            .limit(10)
            .all()
        )
        return [row.content for row in rows]

    def create_workflow_episode(
        self,
        customer_id: str,
        source_event_id: str,
        workflow_state: dict,
    ) -> EpisodicMemory:
        return EpisodicMemory(
            customer_id=customer_id,
            agent_name="journey_orchestrator_agent",
            memory_type="episodic",
            source_event_id=source_event_id,
            content={
                "workflow_id": workflow_state["workflow_id"],
                "correlation_id": workflow_state["correlation_id"],
                "life_events": workflow_state["life_events"],
                "needs": workflow_state["needs"],
                "mapped_services": workflow_state["mapped_services"],
                "adoption_journey": workflow_state["adoption_journey"],
                "feedback": {},
            },
        )