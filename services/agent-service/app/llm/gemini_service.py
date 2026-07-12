from app.core.config import settings


class GeminiExplanationService:
    def generate_explanation(self, workflow_state: dict) -> dict | None:
        if not settings.gemini_api_key:
            return None

        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)

            prompt = f"""
You are Nivara's explanation layer.

Production rules:
- Do not create new recommendations.
- Do not remove recommendations.
- Do not change priorities.
- Do not invent SBI products.
- Explain only the deterministic workflow output.
- Keep the explanation clear, helpful, and non-alarming.

Workflow output:
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