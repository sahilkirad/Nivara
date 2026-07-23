from app.rules.rule_registry import apply_sbi_mapping_rules


class SBIServiceMapperAgent:
    name = "sbi_service_mapper_agent"

    def analyze(self, workflow_state: dict) -> dict:
        recommendations = apply_sbi_mapping_rules(workflow_state.get("needs", []))
        semantic_index = self._build_semantic_index(workflow_state["memory"]["semantic"])

        enriched_recommendations = []
        for recommendation in recommendations:
            recommended_services = self._dedupe_strings(
                recommendation.get("recommended_services", [])
            )
            service_knowledge = self._find_unique_service_knowledge(
                recommended_services,
                semantic_index,
            )

            enriched_recommendations.append({
                **recommendation,
                "recommended_services": recommended_services,
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
            product_name = str(item.get("product_name", "")).strip().lower()
            if product_name:
                index[product_name] = item

            for alias in item.get("aliases", []):
                normalized_alias = str(alias).strip().lower()
                if normalized_alias:
                    index[normalized_alias] = item

        return index

    def _find_unique_service_knowledge(
        self,
        recommended_services: list[str],
        semantic_index: dict,
    ) -> list[dict]:
        unique_items = {}
        for service in recommended_services:
            normalized_service = service.strip().lower()
            matched = [
                item for key, item in semantic_index.items()
                if key in normalized_service or normalized_service in key
            ]

            for item in matched:
                product_name = str(item.get("product_name", "")).strip().lower()
                if product_name:
                    unique_items[product_name] = item

        return list(unique_items.values())

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        seen = set()
        deduped = []

        for value in values:
            normalized_value = value.strip().lower()
            if normalized_value and normalized_value not in seen:
                seen.add(normalized_value)
                deduped.append(value)

        return deduped