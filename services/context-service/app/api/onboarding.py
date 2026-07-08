from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import OnboardingService


router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# use only the prefix so final api path= POST /onboarding
@router.post("", response_model=OnboardingResponse, status_code=201)
def create_onboarding_context(
    request: OnboardingRequest,
    db: Session = Depends(get_db),
) -> OnboardingResponse:
    service = OnboardingService(db)
    return service.create_onboarding_context(request)