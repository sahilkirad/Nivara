# This builder creates the payload for customer.context.created events.
from app.schemas import OnboardingRequest


class CustomerContextBuilder:
    def build_safe_event_payload(
        self,
        request: OnboardingRequest,
        *,
        customer_id: str,
        financial_profile_id: str,
        consent_snapshot_id: str,
    ) -> dict:
        return {
            "customer_id": customer_id,
            "financial_profile_id": financial_profile_id,
            "consent_snapshot_id": consent_snapshot_id,
            "goals": request.goals,
            "risk_preference": request.risk_preference,
            "optional_sbi_signals_allowed": request.consent.optional_sbi_signals_allowed,
        }