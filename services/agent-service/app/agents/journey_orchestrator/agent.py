from datetime import datetime, timezone
from uuid import uuid4

from app.rules.rule_registry import apply_journey_sequence_rules


class JourneyOrchestratorAgent:
    name = "journey_orchestrator_agent"

    def initialize_workflow_state(
        self,
        context: dict,
        source_event_id: str,
        correlation_id: str,
        episodic_memory: list[dict],
        semantic_memory: list[dict],
    ) -> dict:
        workflow_state = {
            "workflow_id": str(uuid4()),
            "customer_id": context.get("customer_id"),
            "source_event_id": source_event_id,
            "correlation_id": correlation_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "memory": {
                "episodic": episodic_memory,
                "semantic": semantic_memory,
            },
            "life_events": [],
            "needs": [],
            "mapped_services": [],
            "adoption_journey": [],
            "explainability": {
                "decision_source": "centralized_deterministic_rule_registry",
                "rules_applied": [],
                "agent_trace": [],
                "llm_used_for_explanation": False,
                "llm_explanation": None,
            },
        }

        self.record_agent_step(
            workflow_state,
            self.name,
            "started",
            "Journey Orchestrator initialized internal workflow state.",
        )
        return workflow_state

    def record_agent_step(
        self,
        workflow_state: dict,
        agent_name: str,
        status: str,
        summary: str,
    ) -> dict:
        workflow_state["explainability"]["agent_trace"].append({
            "agent": agent_name,
            "status": status,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return workflow_state

    def create_adoption_journey(self, workflow_state: dict) -> dict:
        workflow_state["adoption_journey"] = apply_journey_sequence_rules(
            needs=workflow_state.get("needs", []),
            recommendations=workflow_state.get("mapped_services", []),
        )
        self.record_agent_step(
            workflow_state,
            self.name,
            "completed",
            "Journey Orchestrator created personalized adoption journey.",
        )
        return workflow_state

    def finalize_workflow_state(
        self,
        workflow_state: dict,
        llm_explanation: dict | None = None,
    ) -> dict:
        workflow_state["status"] = "completed"
        workflow_state["completed_at"] = datetime.now(timezone.utc).isoformat()
        workflow_state["explainability"]["llm_used_for_explanation"] = llm_explanation is not None
        workflow_state["explainability"]["llm_explanation"] = llm_explanation

        self.record_agent_step(
            workflow_state,
            self.name,
            "completed",
            "Journey Orchestrator finalized workflow state.",
        )
        return workflow_state