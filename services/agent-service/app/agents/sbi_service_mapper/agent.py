from app.rules.rule_registry import apply_sbi_mapping_rules


class SBIServiceMapperAgent:
    name = "sbi_service_mapper_agent"

    def analyze(self, workflow_state: dict) -> dict:
        recommendations = apply_sbi_mapping_rules(workflow_state.get("needs", []))
        semantic_index = self._build_semantic_index(workflow_state["memory"]["semantic"])

        enriched_recommendations = []
        for recommendation in recommendations:
            service_knowledge = []
            for service in recommendation.get("recommended_services", []):
                normalized_service = service.lower()
                matched = [
                    item for key, item in semantic_index.items()
                    if key in normalized_service or normalized_service in key
                ]
                service_knowledge.extend(matched)

            enriched_recommendations.append({
                **recommendation,
                "service_knowledge": service_knowledge,
            })

        workflow_state["mapped_services"] = enriched_recommendations
        workflow_state["explainability"]["rules_applied"].extend(
            item["rule_id"] for item in enriched_recommendations
        )
        workflow_state["explainability"]["agent_trace"].append({
            "agent": self.name,
            "status": "completed",
            "summary": f"Mapped {len(enriched_recommendations)} needs to SBI services using semantic memory.",
        })

        return workflow_state

    def _build_semantic_index(self, semantic_memory: list[dict]) -> dict:
        index = {}

        for item in semantic_memory:
            product_name = str(item.get("product_name", "")).lower()
            if product_name:
                index[product_name] = item

            for alias in item.get("aliases", []):
                index[str(alias).lower()] = item

        return index