from copy import deepcopy
from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.financial_advisor.agent import FinancialAdvisorAgent
from app.agents.journey_orchestrator.agent import JourneyOrchestratorAgent
from app.agents.life_event_intelligence.agent import LifeEventIntelligenceAgent
from app.agents.sbi_service_mapper.agent import SBIServiceMapperAgent
from app.core.security import field_encryptor
from app.db.models import AgentRun, OutboxEvent
from app.llm.gemini_service import GeminiExplanationService
from app.memory.episodic.episodic_memory_service import EpisodicMemoryService
from app.memory.semantic.semantic_memory_service import SemanticMemoryService


RAW_FINANCIAL_KEYS = {
    "monthly_income",
    "monthly_expenses",
    "savings",
    "investments",
    "insurance_coverage",
}


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

        workflow_state = self._sanitize_workflow_state(workflow_state)

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

        encrypted_financial_context = payload.get("encrypted_financial_context", {})
        if encrypted_financial_context:
            context["financial"] = self._decrypt_financial_context(encrypted_financial_context)

        context.pop("encrypted_financial_context", None)
        return context

    def _decrypt_financial_context(self, encrypted_financial_context: dict) -> dict:
        decrypted = {}

        for key in RAW_FINANCIAL_KEYS:
            encrypted_value = encrypted_financial_context.get(key)
            decrypted[key] = field_encryptor.decrypt(encrypted_value)

        return decrypted

    def _sanitize_workflow_state(self, workflow_state: dict) -> dict:
        sanitized_state = deepcopy(workflow_state)

        financial_metrics = sanitized_state.get("financial_metrics", {})
        safe_financial_metrics = self._build_safe_financial_metrics(financial_metrics)

        sanitized_state["context"].pop("financial", None)
        sanitized_state["financial_metrics"] = safe_financial_metrics

        for need in sanitized_state.get("needs", []):
            need["evidence"] = self._sanitize_evidence(need.get("evidence", {}), safe_financial_metrics)

        for mapped_service in sanitized_state.get("mapped_services", []):
            mapped_service["evidence"] = self._sanitize_evidence(
                mapped_service.get("evidence", {}),
                safe_financial_metrics,
            )

        return sanitized_state

    def _build_safe_financial_metrics(self, financial_metrics: dict) -> dict:
        return {
            "expense_cover_months": financial_metrics.get("expense_cover_months", 0),
            "expense_ratio": financial_metrics.get("expense_ratio", 0),
            "monthly_surplus_band": self._amount_band(financial_metrics.get("monthly_surplus", 0)),
            "income_available": financial_metrics.get("monthly_income", 0) > 0,
            "expenses_available": financial_metrics.get("monthly_expenses", 0) > 0,
            "savings_available": financial_metrics.get("savings", 0) > 0,
            "investments_available": financial_metrics.get("investments", 0) > 0,
            "insurance_coverage_present": financial_metrics.get("insurance_coverage", 0) > 0,
        }

    def _sanitize_evidence(self, evidence: dict, safe_financial_metrics: dict) -> dict:
        sanitized_evidence = {
            key: value
            for key, value in evidence.items()
            if key not in RAW_FINANCIAL_KEYS and key != "monthly_surplus"
        }

        if any(key in evidence for key in RAW_FINANCIAL_KEYS):
            sanitized_evidence.update(safe_financial_metrics)

        return sanitized_evidence

    def _amount_band(self, value: object) -> str:
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0

        if amount <= 0:
            return "none"
        if amount < 10000:
            return "low"
        if amount < 50000:
            return "medium"
        return "high"

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