# This builder creates the payload for customer.context.created events.
from app.core.security import field_encryptor
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
            "encrypted_financial_context": {
                "monthly_income": field_encryptor.encrypt(self._stringify_number(request.financial.monthly_income)),
                "monthly_expenses": field_encryptor.encrypt(self._stringify_number(request.financial.monthly_expenses)),
                "savings": field_encryptor.encrypt(self._stringify_number(request.financial.savings)),
                "investments": field_encryptor.encrypt(self._stringify_number(request.financial.investments)),
                "insurance_coverage": field_encryptor.encrypt(
                    self._stringify_number(request.financial.insurance_coverage)
                ),
            },
        }

    def _stringify_number(self, value: float | None) -> str | None:
        if value is None:
            return None
        return str(value)