from uuid import UUID

from pydantic import BaseModel, Field


class PersonalInfoIn(BaseModel):
    name: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    occupation: str | None = None
    marital_status: str | None = None
    city: str | None = None


class FinancialInfoIn(BaseModel):
    monthly_income: float | None = Field(default=None, ge=0)
    monthly_expenses: float | None = Field(default=None, ge=0)
    savings: float | None = Field(default=None, ge=0)
    investments: float | None = Field(default=None, ge=0)
    insurance_coverage: float | None = Field(default=None, ge=0)


class ConsentIn(BaseModel):
    optional_sbi_signals_allowed: bool = False
    consent_text: str | None = None


class OnboardingRequest(BaseModel):
    personal: PersonalInfoIn
    financial: FinancialInfoIn
    goals: list[str] = Field(default_factory=list)
    risk_preference: str | None = None
    consent: ConsentIn = Field(default_factory=ConsentIn)


class OnboardingResponse(BaseModel):
    customer_id: UUID
    context_id: UUID
    financial_profile_id: UUID
    consent_snapshot_id: UUID
    correlation_id: UUID
    status: str