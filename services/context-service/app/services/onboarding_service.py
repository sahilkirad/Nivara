from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import field_encryptor
from app.events.contracts import EventEnvelope
from app.models import AuditLog, ConsentSnapshot, FinancialProfile, Goal, OutboxEvent, User
from app.schemas import OnboardingRequest, OnboardingResponse
from app.services.context_builder import CustomerContextBuilder


class OnboardingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.context_builder = CustomerContextBuilder()

    def create_onboarding_context(self, request: OnboardingRequest) -> OnboardingResponse:
        correlation_id = uuid4()

        user = User(
            name_encrypted=field_encryptor.encrypt(request.personal.name),
            age=request.personal.age,
            occupation=request.personal.occupation,
            marital_status=request.personal.marital_status,
            city_encrypted=field_encryptor.encrypt(request.personal.city),
        )
        self.db.add(user)
        self.db.flush()

        financial_profile = FinancialProfile(
            user_id=user.id,
            monthly_income_encrypted=field_encryptor.encrypt(self._stringify_number(request.financial.monthly_income)),
            monthly_expenses_encrypted=field_encryptor.encrypt(self._stringify_number(request.financial.monthly_expenses)),
            savings_encrypted=field_encryptor.encrypt(self._stringify_number(request.financial.savings)),
            investments_encrypted=field_encryptor.encrypt(self._stringify_number(request.financial.investments)),
            insurance_coverage_encrypted=field_encryptor.encrypt(
                self._stringify_number(request.financial.insurance_coverage)
            ),
            risk_preference=request.risk_preference,
        )
        self.db.add(financial_profile)

        for index, goal_name in enumerate(request.goals, start=1):
            self.db.add(
                Goal(
                    user_id=user.id,
                    goal_name=goal_name,
                    priority=index,
                )
            )

        consent_snapshot = ConsentSnapshot(
            user_id=user.id,
            optional_sbi_signals_allowed=request.consent.optional_sbi_signals_allowed,
            consent_text=request.consent.consent_text,
        )
        self.db.add(consent_snapshot)
        self.db.flush()

        safe_payload = self.context_builder.build_safe_event_payload(
            request,
            customer_id=str(user.id),
            financial_profile_id=str(financial_profile.id),
            consent_snapshot_id=str(consent_snapshot.id),
        )

        event = EventEnvelope(
            correlation_id=correlation_id,
            customer_id=user.id,
            event_type="customer.context.created",
            payload=safe_payload,
        )

        self.db.add(
            OutboxEvent(
                id=event.event_id,
                event_type=event.event_type,
                aggregate_id=user.id,
                correlation_id=correlation_id,
                payload=event.model_dump(mode="json"),
            )
        )

        self.db.add(
            AuditLog(
                actor_id=user.id,
                action="customer_context_created",
                entity_type="customer_context",
                entity_id=user.id,
                correlation_id=correlation_id,
                metadata_json={
                    "has_financial_profile": True,
                    "goals_count": len(request.goals),
                    "optional_sbi_signals_allowed": request.consent.optional_sbi_signals_allowed,
                },
            )
        )

        self.db.commit()

        return OnboardingResponse(
            customer_id=user.id,
            context_id=user.id,
            financial_profile_id=financial_profile.id,
            consent_snapshot_id=consent_snapshot.id,
            correlation_id=correlation_id,
            status="created",
        )

    def _stringify_number(self, value: float | None) -> str | None:
        if value is None:
            return None
        return str(value)