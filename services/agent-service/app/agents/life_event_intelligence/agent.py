from app.rules.rule_registry import apply_life_event_rules


class LifeEventIntelligenceAgent:
    name = "life_event_intelligence_agent"

    def analyze(self, workflow_state: dict) -> dict:
        life_events = apply_life_event_rules(workflow_state["context"])
        workflow_state["life_events"] = life_events

        workflow_state["explainability"]["rules_applied"].extend(
            event["rule_id"] for event in life_events
        )
        workflow_state["explainability"]["agent_trace"].append({
            "agent": self.name,
            "status": "completed",
            "summary": f"Detected {len(life_events)} life event signals.",
        })

        return workflow_state