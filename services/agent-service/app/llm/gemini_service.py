from app.core.config import settings


class GeminiExplanationService:
    def generate_explanation(self, workflow_state: dict) -> dict | None:
        if not settings.gemini_api_key:
            return None

        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)

            prompt = f"""
You are Nivara's explanation layer for a financial guidance platform.

Strict production rules:
- You are not the decision maker.
- Do not create new recommendations.
- Do not remove recommendations.
- Do not change priorities.
- Do not invent SBI products, rates, returns, eligibility rules, or guarantees.
- Explain only the deterministic workflow output.
- Use the recommendation fields exactly: need, why_now, evidence, recommended_services, benefit, next_best_action, caution.
- Keep the explanation clear, specific, and useful for a retail banking customer.
- Avoid technical AI language.
- Do not expose or infer raw salary, raw expenses, raw savings, or sensitive PII.
- Always include a safety reminder to verify details through official SBI channels.

Output style:
- Start with a short personalized summary.
- Then explain the top priorities in order.
- For each priority, explain why it matters now, what service helps, and what action the customer should take.
- Keep the tone calm, trustworthy, and guidance-oriented.

Deterministic workflow output:
{workflow_state}
"""

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )

            return {
                "provider": "gemini",
                "model": settings.gemini_model,
                "status": "completed",
                "text": response.text,
            }

        except Exception as exc:
            return {
                "provider": "gemini",
                "model": settings.gemini_model,
                "status": "failed",
                "error": str(exc),
            }