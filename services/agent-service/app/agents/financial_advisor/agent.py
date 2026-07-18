from app.rules.rule_registry import apply_financial_need_rules, get_financial_metrics


class FinancialAdvisorAgent:
    name = "financial_advisor_agent"

    def analyze(self, workflow_state: dict) -> dict:
        episodic_memory = workflow_state["memory"]["episodic"]
        needs = apply_financial_need_rules(workflow_state["context"], episodic_memory)

        workflow_state["needs"] = needs
        workflow_state["financial_metrics"] = get_financial_metrics(workflow_state["context"])
        workflow_state["explainability"]["rules_applied"].extend(
            need["rule_id"] for need in needs
        )
        workflow_state["explainability"]["agent_trace"].append({
            "agent": self.name,
            "status": "completed",
            "summary": (
                f"Discovered {len(needs)} financial needs using income, expense, savings, "
                "insurance, goals, risk preference, and episodic memory signals."
            ),
        })

        return workflow_state