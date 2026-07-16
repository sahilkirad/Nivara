from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.financial_advisor.agent import FinancialAdvisorAgent
from app.agents.journey_orchestrator.agent import JourneyOrchestratorAgent
from app.agents.life_event_intelligence.agent import LifeEventIntelligenceAgent
from app.agents.sbi_service_mapper.agent import SBIServiceMapperAgent
from app.db.models import AgentRun, OutboxEvent
from app.llm.gemini_service import GeminiExplanationService
from app.memory.episodic.episodic_memory_service import EpisodicMemoryService
from app.memory.semantic.semantic_memory_service import SemanticMemoryService


class AgentWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.episodic_memory_service = EpisodicMemoryService(db)
        self.semantic_memory_service = SemanticMemoryService(db)
        self.orchestrator = JourneyOrchestratorAgent()
        self.life_event_agent = LifeEventIntelligenceAgent()
        self.financial_advisor_agent = FinancialAdvisorAgent()
        self.sbi_service_mapper_agent = SBIServiceMapperAgent()
        self.llm_service = GeminiExplanationService()

    def run(
        self,
        event_payload: dict,
        source_event_id: str,
        correlation_id: str,
    ) -> dict:
        context = self._extract_context(event_payload)
        customer_id = context.get("customer_id")

        episodic_memory = self.episodic_memory_service.load_customer_memory(customer_id)
        semantic_memory = self.semantic_memory_service.load_product_knowledge()

        workflow_state = self.orchestrator.initialize_workflow_state(
            context=context,
            source_event_id=source_event_id,
            correlation_id=correlation_id,
            episodic_memory=episodic_memory,
            semantic_memory=semantic_memory,
        )

        workflow_state = self.life_event_agent.analyze(workflow_state)
        workflow_state = self.financial_advisor_agent.analyze(workflow_state)
        workflow_state = self.sbi_service_mapper_agent.analyze(workflow_state)
        workflow_state = self.orchestrator.create_adoption_journey(workflow_state)

        llm_explanation = self.llm_service.generate_explanation(workflow_state)
        workflow_state = self.orchestrator.finalize_workflow_state(
            workflow_state,
            llm_explanation=llm_explanation,
        )

        self._persist_workflow(workflow_state)
        return workflow_state

    def _extract_context(self, event_payload: dict) -> dict:
        payload = event_payload.get("payload", event_payload)

        context = payload.get("context", payload)
        context["customer_id"] = str(
            payload.get("customer_id")
            or context.get("customer_id")
            or event_payload.get("customer_id")
        )

        return context

    def _persist_workflow(self, workflow_state: dict) -> None:
        customer_id = self._to_uuid(workflow_state["customer_id"])
        source_event_id = self._to_uuid(workflow_state["source_event_id"])
        correlation_id = self._to_uuid(workflow_state["correlation_id"])

        agent_run = AgentRun(
            customer_id=customer_id,
            source_event_id=source_event_id,
            correlation_id=correlation_id,
            status=workflow_state["status"],
            life_events=workflow_state["life_events"],
            needs=workflow_state["needs"],
            mapped_services=workflow_state["mapped_services"],
            explainability=workflow_state["explainability"],
        )

        episode = self.episodic_memory_service.create_workflow_episode(
            customer_id=str(customer_id),
            source_event_id=str(source_event_id),
            workflow_state=workflow_state,
        )

        outbox_event = OutboxEvent(
            event_type="agent.analysis.completed",
            aggregate_id=customer_id,
            correlation_id=correlation_id,
            status="pending",
            payload={
                "workflow_id": workflow_state["workflow_id"],
                "customer_id": str(customer_id),
                "source_event_id": str(source_event_id),
                "correlation_id": str(correlation_id),
                "life_events": workflow_state["life_events"],
                "needs": workflow_state["needs"],
                "mapped_services": workflow_state["mapped_services"],
                "adoption_journey": workflow_state["adoption_journey"],
                "explainability": workflow_state["explainability"],
            },
        )

        self.db.add(agent_run)
        self.db.add(episode)
        self.db.add(outbox_event)
        self.db.flush()

    def _to_uuid(self, value: str) -> UUID:
        return UUID(str(value))